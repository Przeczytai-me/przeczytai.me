export const pl = {
  metadata: {
    title: "PrzeczytAI.me",
    description:
      "PrzeczytAI.me zamienia zaszumione polskie dokumenty w uporządkowany tekst, SSML i gotową narrację.",
  },
  landing: {
    productName: "PrzeczytAI.me",
    valueProposition:
      "Zamieniaj dowolnie sformatowane polskie dokumenty w uporządkowany tekst i gotową narrację.",
    actions: {
      openApp: "Przejdź do dokumentów",
      signUp: "Utwórz konto",
      signIn: "Zaloguj się",
      viewDocs: "Zobacz dokumentację",
    },
    demo: {
      label: "Przykład pracy aplikacji PrzeczytAI.me",
    },
    docsCallout: {
      text: "Jakieś niejasności? Sprawdź naszą dokumentację.",
    },
    capabilities: {
      heading: "Co robi ta aplikacja?",
      description:
        "Jeden przycisk prowadzi dokument od surowego tekstu do materiału, którego można słuchać, który można czytać i który można pobrać.",
      items: {
        cleanup: {
          title: "Porządkowanie tekstu",
          description:
            "Usuwa szum z dokumentów i przygotowuje materiał do czytania na głos.",
        },
        ssml: {
          title: "Znaczniki SSML",
          description:
            "Dodaje pauzy, akcenty i strukturę potrzebną do naturalnej narracji.",
        },
        voice: {
          title: "Polski głos",
          description:
            "Generuje nagrania dopasowane do polskich dokumentów i dłuższych tekstów.",
        },
        highlighting: {
          title: "Podświetlanie",
          description:
            "Synchronizuje tekst z narracją, żeby łatwiej śledzić czytany fragment.",
        },
        downloads: {
          title: "Pobieranie plików",
          description:
            "Udostępnia gotowe wyniki do dalszej pracy poza aplikacją.",
        },
      },
    },
    supportedInputs: {
      heading: "Obsługiwane formaty",
      availableLabel: "Dostępne",
      plannedLabel: "W planach",
      items: [
        {
          extension: ".txt",
          status: "available",
        },
        {
          extension: ".md",
          status: "available",
        },
        {
          extension: ".pdf",
          status: "planned",
        },
        {
          extension: ".docx",
          status: "planned",
        },
      ],
    },
    footer: {
      copyright: "© 2026 PrzeczytAI.me",
      contactLabel: "Kontakt:",
      contactEmail: "informaks23@gmail.com",
    },
  },
  auth: {
    signIn: {
      title: "Zaloguj się",
      description: "Wróć do swoich dokumentów i gotowych nagrań.",
    },
    signUp: {
      title: "Utwórz konto",
      description: "Zacznij pracę w prywatnej przestrzeni na dokumenty.",
    },
    backToLanding: "Wróć na stronę główną",
    privateWorkspaceNote:
      "Dokumenty są przechowywane w prywatnej przestrzeni użytkownika.",
  },
  app: {
    notImplementedYet: "not implemented yet",
    shell: {
      productName: "PrzeczytAI.me",
      processingStatus: "Brak aktywnego przetwarzania",
      documentTitlePrefix: "Dokument",
      navigation: {
        documents: "Dokumenty",
        newDocument: "Nowy dokument",
        jobs: "Zadania",
        settings: "Ustawienia",
        documentation: "Dokumentacja",
      },
      sidebar: {
        collapseLabel: "Zwiń panel boczny",
        expandLabel: "Rozwiń panel boczny",
      },
      breadcrumbs: {
        label: "Ścieżka dokumentu",
        documents: "Dokumenty",
      },
      toasts: {
        label: "Powiadomienia aplikacji",
        title: "Powiadomienia gotowe",
        description:
          "Tutaj pojawią się informacje o przesyłaniu, przetwarzaniu, pobieraniu i zapisywaniu.",
      },
    },
    documents: {
      heading: "Dokumenty",
      description:
        "Przeglądaj przesłane teksty, statusy przetwarzania i gotowe nagrania.",
      newDocument: "Nowy dokument",
      searchPlaceholder: "Szukaj dokumentu",
      statusFilter: "Wszystkie statusy",
      refresh: "Odśwież",
      refreshing: "Odświeżanie",
      loading: "Ładowanie dokumentów...",
      emptyTitle: "Nie masz jeszcze dokumentów",
      emptyAction: "Dodaj pierwszy dokument",
      next: "Załaduj więcej",
      loadingMore: "Ładowanie",
      summary: {
        total: "Dokumenty",
        processing: "W trakcie",
        ready: "Gotowe",
      },
      row: {
        created: "Utworzono",
        downloadRecording: "MP3",
        downloadText: "Tekst",
        delete: "Usuń",
        deleting: "Usuwanie",
        downloadFailed: "Pobieranie nie powiodło się",
      },
    },
    newDocument: {
      heading: "Nowy dokument",
      description:
        "Dodaj tekst do przetworzenia na uporządkowany materiał i narrację.",
      fileLabel: "Plik źródłowy",
      fileDescription: "Wybierz plik .txt lub .md albo wklej tekst poniżej.",
      selectedFile: "Wybrany plik",
      unsupportedFile: "Obsługiwane są tylko pliki .txt i .md.",
      textPlaceholder: "Wklej tekst dokumentu",
      vendorPlaceholder: "Dostawca głosu (opcjonalnie)",
      voicePlaceholder: "Głos (opcjonalnie)",
      limitNote: "Limit v1:",
      create: "czytAI",
      creating: "Tworzenie",
      created: "Utworzono",
    },
    settings: {
      heading: "Ustawienia",
      description:
        "Ustaw domyślne wartości używane przy kolejnych dokumentach.",
      temporaryDescription:
        "Aktualnie zapis działa lokalnie w tej przeglądarce, dopóki backend nie udostępni profilu ustawień.",
      futureOnlyNotice:
        "Zmiany dotyczą tylko przyszłych dokumentów. Istniejące nagrania i przetworzone teksty nie zostaną zmienione.",
      resetConfirm:
        "Przywrócić domyślne ustawienia? Niezapisane zmiany w formularzu zostaną zastąpione.",
      privacyRetentionTitle: "Retencja nieaktywnych kont",
      privacyRetentionDescription:
        "Dokumenty na nieaktywnych kontach mogą być usuwane po 365 dniach bez aktywności.",
      abbreviationsEmpty: "Nie dodano jeszcze domyślnych odczytów skrótów.",
      actions: {
        addAbbreviation: "Dodaj wiersz",
        deleteAllDocuments: "Usuń wszystkie dokumenty",
        discard: "Odrzuć",
        previewVoice: "Odsłuchaj głos",
        removeAbbreviation: "Usuń wiersz",
        reset: "Przywróć domyślne",
        save: "Zapisz ustawienia",
      },
      fields: {
        abbreviation: "Skrót",
        actions: "Akcje",
        defaultModel: "Domyślny model TTS",
        defaultVoice: "Domyślny polski głos",
        expansion: "Odczyt",
        fallbackModel: "Model zapasowy",
        highlightBehavior: "Podświetlanie zdań",
        playbackSpeed: "Domyślna prędkość",
        pronunciationStyle: "Styl wymowy",
        textFormat: "Format tekstu",
      },
      placeholders: {
        abbreviation: "np. prof.",
        expansion: "np. profesor",
      },
      sections: {
        abbreviations: {
          title: "Odczyty skrótów",
          description:
            "Zapisz domyślne wymowy skrótów, które chcesz stosować w nowych dokumentach.",
        },
        exports: {
          title: "Eksporty",
          description: "Ustaw domyślny format tekstu dla przyszłych eksportów.",
        },
        model: {
          title: "Model czytania",
          description:
            "Wybierz model główny i zapasowy dla nowych zadań przetwarzania.",
        },
        playback: {
          title: "Odtwarzanie",
          description:
            "Dostosuj prędkość startową i zachowanie podświetlania zdań.",
        },
        privacy: {
          title: "Prywatność",
          description:
            "Sprawdź zasady retencji i akcje dotyczące przechowywanych dokumentów.",
          linkLabel: "Polityka prywatności",
        },
        voice: {
          title: "Głos",
          description:
            "Ustaw domyślny polski głos i sposób wymowy dla nowych nagrań.",
        },
      },
      status: {
        discarded: "Zmiany odrzucone.",
        editing: "Masz niezapisane zmiany.",
        ready: "Ustawienia gotowe.",
        reset: "Domyślne ustawienia przywrócone i zapisane.",
        saved: "Ustawienia zapisane.",
      },
      unsupported: {
        abbreviations:
          "Te reguły zapisują się w localStorage przeglądarki po użyciu paska zapisu. Backend nie obsługuje jeszcze globalnych odczytów skrótów.",
        deleteAllDocuments:
          "Akcja będzie dostępna po dodaniu bezpiecznego endpointu usuwania wszystkich dokumentów.",
        voicePreview:
          "Podgląd głosu wymaga endpointu generowania krótkiej próbki audio.",
      },
      unsavedBar: {
        message: "Masz niezapisane zmiany w ustawieniach.",
      },
    },
  },
} as const;
