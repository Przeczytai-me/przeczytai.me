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
  },
} as const;
