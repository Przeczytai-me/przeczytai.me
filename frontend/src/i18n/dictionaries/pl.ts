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
      viewDocs: "Centrum pomocy",
    },
    demo: {
      label: "Przykład pracy aplikacji PrzeczytAI.me",
    },
    docsCallout: {
      text: "Potrzebujesz pomocy? Zajrzyj do prostych przewodników po aplikacji.",
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
  docs: {
    backToHome: "Strona główna",
    uiTranslations: {
      "Close Sidebar(sidebar)(aria-label)": "Zamknij panel boczny",
      "Collapse Sidebar(sidebar)(aria-label)": "Zwiń panel boczny",
      "Copy Anchor Link(heading anchor)(aria-label)":
        "Kopiuj odnośnik do sekcji",
      "Next Page(pagination)": "Następna strona",
      "On this page(table of contents)": "Na tej stronie",
      "Open Sidebar(sidebar)(aria-label)": "Otwórz panel boczny",
      "Previous Page(pagination)": "Poprzednia strona",
    },
  },
  app: {
    notImplementedYet: "not implemented yet",
    shell: {
      productName: "PrzeczytAI.me",
      processingStatus: "Brak aktywnego przetwarzania",
      documentTitlePrefix: "Dokument",
      navigation: {
        account: "Konto",
        documents: "Dokumenty",
        newDocument: "Nowy dokument",
        jobs: "Zadania",
        settings: "Ustawienia",
        documentation: "Centrum pomocy",
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
    reader: {
      header: {
        back: "Wróć do dokumentów",
      },
      loading: "Ładowanie dokumentu...",
      loadError: {
        title: "Nie udało się otworzyć dokumentu",
        description:
          "Dokument nie istnieje albo nie masz dostępu do jego zawartości.",
        retry: "Spróbuj ponownie",
      },
      processing: {
        title: "Dokument jest jeszcze przetwarzany",
        description:
          "Nagranie i dane synchronizacji nie są jeszcze gotowe. Możesz sprawdzić bieżący etap na stronie zadań.",
        jobs: "Przejdź do zadań",
        documents: "Wróć do dokumentów",
      },
      text: {
        title: "Treść dokumentu",
        description:
          "Czytaj tekst i wybierz zdanie, aby przejść do odpowiedniego miejsca w nagraniu.",
        loading: "Ładowanie tekstu źródłowego...",
        unavailableTitle: "Brak pliku źródłowego",
        unavailableDescription:
          "Nie udało się pobrać oryginalnego tekstu. Pozostałe gotowe pliki nadal możesz pobrać.",
        emptyTitle: "Dokument nie zawiera tekstu",
        emptyDescription:
          "Z pliku źródłowego nie udało się odczytać treści. Ponów generowanie albo dodaj nowy dokument.",
        noSyncTitle: "Synchronizacja zdań jest niedostępna",
        noSyncDescription:
          "Tekst możesz nadal czytać i odsłuchiwać, ale wybieranie zdań oraz automatyczne podświetlanie są wyłączone.",
        syncLoading: "Ładowanie synchronizacji zdań...",
        currentSentence: "Aktualnie odtwarzane zdanie",
      },
      details: {
        title: "Szczegóły dokumentu",
        description:
          "Informacje o pliku, nagraniu i ostatnim przetwarzaniu dokumentu.",
        processingTitle: "Przetwarzanie",
        downloadsTitle: "Pliki do pobrania",
        downloadsDescription:
          "Pobierz gotowe wyniki albo zachowaną treść źródłową.",
        status: "Status",
        created: "Utworzono",
        updated: "Ostatnia zmiana",
        characters: "Liczba znaków",
        voice: "Głos",
        model: "Model",
        duration: "Długość nagrania",
        unknown: "Brak danych",
        statuses: {
          completed: "Gotowy",
          failed: "Niepowodzenie",
          failedToStart: "Nie uruchomiono",
          processing: "Przetwarzanie",
        },
        actions: {
          downloadMp3: "Pobierz MP3",
          downloadCorrected: "Pobierz poprawiony tekst",
          downloadOriginal: "Pobierz plik źródłowy",
          retry: "Ponów generowanie",
          retrying: "Ponawianie...",
        },
        downloadError: "Nie udało się pobrać pliku.",
        retryError: "Nie udało się ponowić generowania.",
      },
      menu: {
        label: "Więcej opcji dokumentu",
        autoHighlight: "Automatyczne podświetlanie",
        details: "Szczegóły dokumentu",
        downloads: "Pliki do pobrania",
        regenerate: "Wygeneruj ponownie",
      },
      regenerate: {
        title: "Wygenerować dokument ponownie?",
        description:
          "Powstanie nowe zadanie przetwarzania. Obecny poprawiony tekst i nagranie pozostaną dostępne, dopóki nowa próba nie zakończy się powodzeniem.",
        warning:
          "Nie uruchamiaj ponownego generowania, jeśli nie chcesz rozpocząć kolejnej próby przetwarzania.",
        cancel: "Anuluj",
        confirm: "Wygeneruj ponownie",
      },
      dialog: {
        close: "Zamknij",
      },
      failure: {
        mp3Title: "Nagranie MP3 nie jest dostępne",
        mp3Description:
          "Generowanie nagrania nie powiodło się. Możesz pobrać dostępne pliki tekstowe i ponowić próbę.",
      },
      highlights: {
        label: "Podświetlaj odtwarzane zdanie",
      },
      player: {
        label: "Odtwarzacz dokumentu",
        play: "Odtwórz",
        pause: "Wstrzymaj",
        previous: "Poprzednie zdanie",
        next: "Następne zdanie",
        seek: "Pozycja nagrania",
        speed: "Prędkość odtwarzania",
        speedValue: "×",
        audioError: "Nie udało się odtworzyć nagrania.",
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
    account: {
      heading: "Konto",
      description:
        "Zarządzaj profilem, metodami logowania, aktywną sesją i danymi konta.",
      email: {
        title: "Adres e-mail",
        description: "Adres używany do logowania i kontaktu z aplikacją.",
        label: "Podstawowy adres e-mail",
        loading: "Ładowanie adresu e-mail...",
        unavailable: "Brak podstawowego adresu e-mail",
        manageAccount: "Zarządzaj profilem i metodami logowania",
      },
      session: {
        title: "Sesja",
        description:
          "Wylogowanie zakończy bieżącą sesję i przeniesie Cię na stronę główną.",
        signOut: "Wyloguj się",
      },
      data: {
        title: "Prywatność i usunięcie danych",
        description:
          "Sprawdź politykę prywatności albo wyślij prośbę o usunięcie konta i powiązanych danych.",
        privacyPolicy: "Polityka prywatności",
        deletionRequest: "Poproś o usunięcie konta i danych",
        deletionRequestSubject: "Prośba o usunięcie konta i danych",
        deletionRequestNote:
          "Bezpośrednie usuwanie wszystkich danych nie jest jeszcze obsługiwane przez backend. Prośba zostanie wysłana do zespołu PrzeczytAI.me.",
      },
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
