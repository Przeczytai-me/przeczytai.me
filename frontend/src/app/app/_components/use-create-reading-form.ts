"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useReducer } from "react";
import { dictionary } from "@/i18n/dictionaries";
import { createReading } from "@/lib/api";
import { isSupportedDocumentFile } from "@/lib/file-constants";
import type { CreateReadingFormState } from "./create-reading-form";

const copy = dictionary.app.newDocument;

const initialState: CreateReadingFormState = {
  text: "",
  vendor: "",
  voice: "",
  selectedFileName: null,
  fileError: null,
};

type CreateReadingAction =
  | { type: "fileRejected"; error: string }
  | { type: "fileSelected"; fileName: string; text: string }
  | { type: "reset" }
  | { type: "setText"; text: string }
  | { type: "setVendor"; vendor: string }
  | { type: "setVoice"; voice: string };

const createReadingReducer = (
  state: CreateReadingFormState,
  action: CreateReadingAction,
): CreateReadingFormState => {
  switch (action.type) {
    case "fileRejected":
      return {
        ...state,
        fileError: action.error,
        selectedFileName: null,
      };
    case "fileSelected":
      return {
        ...state,
        fileError: null,
        selectedFileName: action.fileName,
        text: action.text,
      };
    case "reset":
      return initialState;
    case "setText":
      return { ...state, text: action.text };
    case "setVendor":
      return { ...state, vendor: action.vendor };
    case "setVoice":
      return { ...state, voice: action.voice };
  }
};

export const useCreateReadingForm = () => {
  const queryClient = useQueryClient();
  const [state, dispatch] = useReducer(createReadingReducer, initialState);

  const mutation = useMutation({
    mutationFn: () =>
      createReading({
        original_text: state.text,
        vendor: state.vendor || null,
        voice: state.voice || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["readings"] });
      dispatch({ type: "reset" });
    },
  });

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    if (!isSupportedDocumentFile(file)) {
      dispatch({ type: "fileRejected", error: copy.unsupportedFile });
      event.target.value = "";
      return;
    }

    const fileText = await file.text();
    dispatch({ type: "fileSelected", fileName: file.name, text: fileText });
  };

  return {
    error: mutation.error,
    handleFileChange,
    handleSubmit: () => mutation.mutate(),
    isPending: mutation.isPending,
    isSuccess: mutation.isSuccess,
    readingId: mutation.data?.id,
    setText: (text: string) => dispatch({ type: "setText", text }),
    setVendor: (vendor: string) => dispatch({ type: "setVendor", vendor }),
    setVoice: (voice: string) => dispatch({ type: "setVoice", voice }),
    state,
  };
};
