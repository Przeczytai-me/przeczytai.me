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
      navigationLabel: "Informacje prawne",
      privacy: "Prywatność",
      terms: "Warunki korzystania",
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
  legal: {
    common: {
      productName: "PrzeczytAI.me",
      navigationLabel: "Nawigacja publiczna",
      backToHome: "Wróć na stronę główną",
      helpCenter: "Centrum pomocy",
      signIn: "Zaloguj się",
      onThisPage: "Na tej stronie",
      draftLabel: "Wersja robocza",
      draftTitle: "Treść oczekuje na zatwierdzenie",
      draftDescription:
        "Ta strona opisuje aktualne założenia produktu. Nie jest jeszcze ostatecznym dokumentem prawnym.",
      updatedLabel: "Stan informacji",
      updatedAt: "27 lipca 2026",
      contactTitle: "Pytania o dane lub zasady korzystania",
      contactDescription:
        "Napisz do nas, jeśli chcesz uzyskać informacje o swoich danych, zgłosić prośbę o ich usunięcie albo wyjaśnić zasady korzystania z usługi.",
      contactAction: "Napisz do nas",
    },
    privacy: {
      metadata: {
        title: "Prywatność | PrzeczytAI.me",
        description:
          "Informacje o przetwarzaniu dokumentów, przechowywaniu danych i planowanej retencji w PrzeczytAI.me.",
      },
      eyebrow: "Prywatność",
      title: "Jak PrzeczytAI.me pracuje z Twoimi danymi",
      description:
        "Przesłane dokumenty służą do przygotowania uporządkowanego tekstu i nagrania. Poniżej wyjaśniamy, jakie informacje są potrzebne do działania produktu i które zasady wymagają jeszcze formalnego zatwierdzenia.",
      sections: [
        {
          id: "zakres-danych",
          title: "Jakie dane wykorzystujemy",
          paragraphs: [
            "Do obsługi konta używamy informacji potrzebnych do logowania, takich jak adres e-mail i identyfikator użytkownika. Uwierzytelnianie obsługuje Clerk.",
            "Podczas tworzenia nagrania przetwarzamy treść przesłanego pliku, jego podstawowe informacje oraz utworzone wyniki: poprawiony tekst, nagranie i dane potrzebne do synchronizacji odtwarzania.",
          ],
        },
        {
          id: "cel-przetwarzania",
          title: "Po co przetwarzamy dokumenty",
          paragraphs: [
            "Treść dokumentu jest używana do uporządkowania tekstu, zastosowania podanych odczytów skrótów, wygenerowania narracji i udostępnienia plików do pobrania.",
            "Nie wykorzystujemy treści dokumentu do określania limitów subskrypcji ani innych zasad rozliczeń, ponieważ te zasady nie zostały jeszcze ustalone dla wersji 1.",
          ],
        },
        {
          id: "dostep-i-dostawcy",
          title: "Dostęp i zewnętrzni dostawcy",
          paragraphs: [
            "Dokumenty i wyniki są przypisane do zalogowanego użytkownika. Chronione operacje aplikacji wymagają aktywnej sesji, a pliki nie są udostępniane jako publiczne zasoby.",
            "Aby utworzyć narrację, treść może zostać przekazana dostawcy syntezy mowy wybranemu dla danego zadania. Zakres dodatkowego przetwarzania AI zależy od konfiguracji produktu i zostanie doprecyzowany w zatwierdzonej polityce.",
          ],
        },
        {
          id: "przechowywanie",
          title: "Przechowywanie i planowana retencja",
          paragraphs: [
            "Założenie wersji 1 przewiduje usuwanie plików źródłowych, przetworzonego tekstu i nagrań po 365 dniach bez aktywności dotyczącej dokumentu.",
            "Automatyczne egzekwowanie tego okresu nie zostało jeszcze potwierdzone w środowisku produkcyjnym. Do czasu wdrożenia i zatwierdzenia tej zasady traktuj 365 dni jako planowany okres retencji, a nie gwarantowany termin automatycznego usunięcia.",
          ],
        },
        {
          id: "prawa-i-usuniecie",
          title: "Dostęp do danych i usunięcie",
          paragraphs: [
            "Możesz pobierać swoje dostępne pliki z poziomu aplikacji. Usunięcie wszystkich danych konta nie ma jeszcze kompletnej samoobsługowej ścieżki.",
            "Aby poprosić o usunięcie konta i powiązanych danych albo uzyskać informacje o ich przetwarzaniu, skontaktuj się z zespołem PrzeczytAI.me.",
          ],
        },
      ],
    },
    terms: {
      metadata: {
        title: "Warunki korzystania | PrzeczytAI.me",
        description:
          "Robocza informacja o planowanym zakresie warunków korzystania z PrzeczytAI.me.",
      },
      eyebrow: "Warunki korzystania",
      title: "Zasady korzystania z PrzeczytAI.me",
      description:
        "Ostateczny regulamin nie został jeszcze zatwierdzony. Ta strona porządkuje zakres zasad, które muszą zostać przyjęte przed publicznym uruchomieniem usługi.",
      sections: [
        {
          id: "status-dokumentu",
          title: "Status tej strony",
          paragraphs: [
            "Poniższe informacje są opisem planowanego działania produktu, a nie wiążącym regulaminem świadczenia usług. Finalna treść zostanie opublikowana po zakończeniu przeglądu prawnego i produktowego.",
          ],
        },
        {
          id: "zakres-uslugi",
          title: "Planowany zakres usługi",
          paragraphs: [
            "PrzeczytAI.me ma umożliwiać przesyłanie obsługiwanych dokumentów, porządkowanie ich treści, generowanie narracji oraz pobieranie dostępnych wyników.",
            "Szczegóły planów, płatności, limitów dokumentów, limitów ponawiania i gwarantowanej dostępności nie są jeszcze określone i nie stanowią części tej wersji roboczej.",
          ],
        },
        {
          id: "odpowiedzialnosc-uzytkownika",
          title: "Odpowiedzialność użytkownika",
          paragraphs: [
            "Przed publikacją regulamin powinien określić, że użytkownik odpowiada za prawo do przesyłania i przetwarzania treści oraz za bezpieczeństwo swojego konta.",
            "Szczegółowe zasady dotyczące treści zabronionych, praw osób trzecich i niedozwolonego użycia wymagają zatwierdzenia w osobnej polityce bezpiecznego korzystania.",
          ],
        },
        {
          id: "wyniki-i-dostawcy",
          title: "Wyniki przetwarzania i dostawcy",
          paragraphs: [
            "Wyniki automatycznego porządkowania tekstu i syntezy mowy mogą wymagać sprawdzenia przez użytkownika. Produkt nie powinien obiecywać bezbłędnego odczytu każdego dokumentu.",
            "Do wygenerowania nagrania usługa może korzystać z zewnętrznych dostawców syntezy mowy. Ich ostateczna lista i związane z nią zasady przetwarzania zostaną opisane w zatwierdzonej dokumentacji.",
          ],
        },
        {
          id: "zmiany-i-kontakt",
          title: "Zmiany i kontakt",
          paragraphs: [
            "Przed rozpoczęciem świadczenia usługi na podstawie regulaminu użytkownicy powinni otrzymać finalną treść, datę wejścia w życie i informację o istotnych zmianach.",
            "Do tego czasu pytania o planowane zasady korzystania można kierować bezpośrednio do zespołu PrzeczytAI.me.",
          ],
        },
      ],
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
        "Prześlij plik, sprawdź wykrytą treść i rozpocznij tworzenie narracji.",
      upload: {
        title: "Prześlij plik źródłowy",
        description: "Przeciągnij tutaj jeden plik .txt lub .md.",
        inputLabel: "Wybierz plik z urządzenia",
        supportedFormats: "Obsługiwane formaty: .txt i .md",
        limitNote:
          "W wersji 1 dokument może zawierać maksymalnie 10 000 znaków.",
      },
      preview: {
        title: "Podgląd źródła",
        description: "Sprawdź właściwości pliku i początek odczytanej treści.",
        fileName: "Nazwa pliku",
        fileType: "Typ",
        fileSize: "Rozmiar",
        characterCount: "Wykryte znaki",
        content: "Początek treści",
        removeFile: "Usuń wybrany plik",
        truncated: "Podgląd został skrócony.",
        types: {
          markdown: "Markdown (.md)",
          text: "Tekst (.txt)",
        },
      },
      abbreviations: {
        title: "Odczyty skrótów",
        description:
          "PrzeczytAI.me próbuje poprawnie czytać skróty automatycznie. Jeśli potrzebujesz pełnej kontroli, podaj dokładny sposób odczytu.",
        scope:
          "Odczyty dodane tutaj dotyczą tylko tego dokumentu. Domyślne odczyty możesz zapisać w ustawieniach.",
        empty: "Nie dodano odczytów tylko dla tego dokumentu.",
        abbreviationLabel: "Skrót",
        readAsLabel: "Czytaj jako",
        abbreviationPlaceholder: "np. prof.",
        readAsPlaceholder: "np. profesor",
        add: "Dodaj odczyt",
        remove: "Usuń odczyt",
      },
      errors: {
        singleFile: "Prześlij dokładnie jeden plik.",
        unsupportedFile:
          "Ten format nie jest obsługiwany. Wybierz plik z rozszerzeniem .txt lub .md.",
        readFailed:
          "Nie udało się odczytać pliku. Wybierz go ponownie albo użyj innego pliku.",
        emptyFile: "Plik nie zawiera tekstu do przetworzenia.",
        tooLong: "Wykryto {count} znaków. Limit wersji 1 wynosi 10 000 znaków.",
        incompleteAbbreviation:
          "Uzupełnij oba pola odczytu skrótu albo usuń ten wiersz.",
        duplicateAbbreviation: "Ten skrót został już dodany.",
        submit:
          "Nie udało się rozpocząć przetwarzania. Sprawdź dane i spróbuj ponownie.",
      },
      submitNote:
        "Po uruchomieniu wrócisz do dokumentów, gdzie zobaczysz bieżący status przetwarzania.",
      create: "czytAI",
      creating: "Uruchamianie...",
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
