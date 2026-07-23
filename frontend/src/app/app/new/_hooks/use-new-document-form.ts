"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useMemo, useReducer, useRef } from "react";
import { useLocalStorage } from "@/hooks/use-local-storage";
import { dictionary } from "@/i18n/dictionaries";
import { createReading } from "@/lib/api";
import {
  getSupportedDocumentExtension,
  isSupportedDocumentFile,
} from "@/lib/file-constants";
import { localStorageKeys } from "@/lib/local-storage-keys";
import { defaultAppSettings, parseAppSettings } from "@/lib/settings-defaults";
import { newDocumentCharacterLimit } from "../utils";

const copy = dictionary.app.newDocument;

export type SelectedDocument = {
  extension: ".txt" | ".md";
  name: string;
  size: number;
  text: string;
};

export type AbbreviationReadingDraft = {
  abbreviation: string;
  id: string;
  readAs: string;
};

type NewDocumentFormState = {
  abbreviationReadings: AbbreviationReadingDraft[];
  fileError: string | null;
  selectedDocument: SelectedDocument | null;
};

type NewDocumentFormAction =
  | {
      type: "abbreviationAdded";
      reading: AbbreviationReadingDraft;
    }
  | {
      type: "abbreviationChanged";
      field: "abbreviation" | "readAs";
      id: string;
      value: string;
    }
  | { type: "abbreviationRemoved"; id: string }
  | { type: "documentRemoved" }
  | { type: "fileRejected"; error: string }
  | { type: "fileSelected"; document: SelectedDocument };

const initialState: NewDocumentFormState = {
  abbreviationReadings: [],
  fileError: null,
  selectedDocument: null,
};

const newDocumentFormReducer = (
  state: NewDocumentFormState,
  action: NewDocumentFormAction,
): NewDocumentFormState => {
  switch (action.type) {
    case "abbreviationAdded":
      return {
        ...state,
        abbreviationReadings: [...state.abbreviationReadings, action.reading],
      };
    case "abbreviationChanged":
      return {
        ...state,
        abbreviationReadings: state.abbreviationReadings.map((reading) =>
          reading.id === action.id
            ? { ...reading, [action.field]: action.value }
            : reading,
        ),
      };
    case "abbreviationRemoved":
      return {
        ...state,
        abbreviationReadings: state.abbreviationReadings.filter(
          (reading) => reading.id !== action.id,
        ),
      };
    case "documentRemoved":
      return { ...state, fileError: null, selectedDocument: null };
    case "fileRejected":
      return { ...state, fileError: action.error, selectedDocument: null };
    case "fileSelected":
      return {
        ...state,
        fileError: null,
        selectedDocument: action.document,
      };
  }
};

export const useNewDocumentForm = () => {
  const queryClient = useQueryClient();
  const router = useRouter();
  const [state, dispatch] = useReducer(newDocumentFormReducer, initialState);
  const fileSelectionSequence = useRef(0);
  const [settings, , hasHydratedSettings] = useLocalStorage(
    localStorageKeys.settings,
    {
      defaultValue: defaultAppSettings,
      parse: parseAppSettings,
    },
  );

  const documentError = getDocumentError(state.selectedDocument);
  const abbreviationErrors = useMemo(
    () => getAbbreviationErrors(state.abbreviationReadings),
    [state.abbreviationReadings],
  );
  const hasAbbreviationErrors = abbreviationErrors.some(Boolean);

  const mutation = useMutation({
    mutationFn: () => {
      if (!state.selectedDocument) {
        throw new Error(copy.errors.singleFile);
      }

      return createReading({
        abbreviation_readings: state.abbreviationReadings
          .filter(
            (reading) => reading.abbreviation.trim() && reading.readAs.trim(),
          )
          .map((reading) => ({
            abbreviation: reading.abbreviation.trim(),
            read_as: reading.readAs.trim(),
          })),
        original_text: state.selectedDocument.text,
        vendor: settings.defaultModel,
        voice: settings.defaultVoice,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["readings"] });
      router.push("/app");
    },
  });

  const handleFilesSelected = async (files: File[]) => {
    mutation.reset();
    const selectionSequence = ++fileSelectionSequence.current;

    if (files.length !== 1) {
      dispatch({ type: "fileRejected", error: copy.errors.singleFile });
      return;
    }

    const [file] = files;
    if (!isSupportedDocumentFile(file)) {
      dispatch({
        type: "fileRejected",
        error: copy.errors.unsupportedFile,
      });
      return;
    }

    try {
      const text = await file.text();
      if (selectionSequence !== fileSelectionSequence.current) {
        return;
      }

      const extension = getSupportedDocumentExtension(file.name);

      if (!extension) {
        dispatch({
          type: "fileRejected",
          error: copy.errors.unsupportedFile,
        });
        return;
      }

      dispatch({
        type: "fileSelected",
        document: {
          extension,
          name: file.name,
          size: file.size,
          text,
        },
      });
    } catch {
      if (selectionSequence === fileSelectionSequence.current) {
        dispatch({ type: "fileRejected", error: copy.errors.readFailed });
      }
    }
  };

  const handleSubmit = () => {
    if (
      !state.selectedDocument ||
      state.fileError ||
      documentError ||
      hasAbbreviationErrors ||
      !hasHydratedSettings
    ) {
      return;
    }

    mutation.mutate();
  };

  return {
    abbreviationErrors,
    addAbbreviationReading: () => {
      mutation.reset();
      dispatch({
        type: "abbreviationAdded",
        reading: createAbbreviationReadingDraft(),
      });
    },
    canSubmit:
      Boolean(state.selectedDocument) &&
      !state.fileError &&
      !documentError &&
      !hasAbbreviationErrors &&
      hasHydratedSettings,
    documentError,
    error: mutation.error,
    handleFilesSelected,
    handleSubmit,
    isPending: mutation.isPending,
    removeAbbreviationReading: (id: string) => {
      mutation.reset();
      dispatch({ type: "abbreviationRemoved", id });
    },
    removeDocument: () => {
      mutation.reset();
      fileSelectionSequence.current += 1;
      dispatch({ type: "documentRemoved" });
    },
    state,
    updateAbbreviationReading: (
      id: string,
      field: "abbreviation" | "readAs",
      value: string,
    ) => {
      mutation.reset();
      dispatch({ type: "abbreviationChanged", field, id, value });
    },
  };
};

const getDocumentError = (document: SelectedDocument | null) => {
  if (!document) {
    return null;
  }

  if (!document.text.trim()) {
    return copy.errors.emptyFile;
  }

  if (document.text.length > newDocumentCharacterLimit) {
    return copy.errors.tooLong.replace(
      "{count}",
      document.text.length.toLocaleString("pl-PL"),
    );
  }

  return null;
};

const getAbbreviationErrors = (readings: AbbreviationReadingDraft[]) => {
  const usedAbbreviations = new Set<string>();

  return readings.map((reading) => {
    const abbreviation = reading.abbreviation.trim();
    const readAs = reading.readAs.trim();

    if (Boolean(abbreviation) !== Boolean(readAs)) {
      return copy.errors.incompleteAbbreviation;
    }

    if (!abbreviation) {
      return null;
    }

    const normalizedAbbreviation = abbreviation.toLocaleLowerCase("pl-PL");
    if (usedAbbreviations.has(normalizedAbbreviation)) {
      return copy.errors.duplicateAbbreviation;
    }

    usedAbbreviations.add(normalizedAbbreviation);
    return null;
  });
};

const createAbbreviationReadingDraft = (): AbbreviationReadingDraft => ({
  abbreviation: "",
  id:
    typeof crypto === "undefined" || !crypto.randomUUID
      ? `document-abbreviation-${Date.now()}`
      : crypto.randomUUID(),
  readAs: "",
});
