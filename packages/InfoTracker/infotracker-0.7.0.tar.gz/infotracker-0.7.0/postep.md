ZAWSZE PIERWSZĄ WYWOŁANĄ KOMENDĄ MUSI BYĆ .\..\infotracker-env\Scripts\Activate.ps1

8 testów failuje (pre existing)

## Status na dziś
- Naprawiono fallback w parserze procedur: ekstrakcja kolumn z `SELECT INTO`/`INSERT INTO` filtruje aliasy tabel i poprawnie obsługuje nazwy kwalifikowane.
- Dla `SELECT * INTO #temp` z dodatkowymi kolumnami usuwamy `*` ze schematu temp (zostają tylko jawne kolumny) — `#LeadTime_STEP4` ma 5 kolumn.
- Dodano testy regresyjne dla `#CTE2` i `#LeadTime_STEP4` w `tests/test_leadtime_regression.py`.
- Rozwinięto `*` z temp źródeł do konkretnych kolumn, jeśli temp schema jest znana (np. `ContractNumber` propaguje się do `#LeadTime_STEP4`).
- `_ns_and_name` rozpoznaje kanoniczne tempy z `.#` i mapuje je do nazw z kontekstem procedury.
- Testy: `pytest -q` → 9 fail (pozostają `test_temp_table_scoping.py` i regresje `test_trialbalance_regression.py`), 156 passed, 3 skipped.
- Zmiany w kodzie: w fallbacku dla `SELECT ... INTO #temp` w procedurach dodane wydobycie projekcji przez sqlglot (`_extract_column_lineage`) przed regexem, żeby lepiej łapać złożone CASE/COALESCE/aliasy.
- Zmiany w kodzie: fallback nie nadpisuje już kolumn z sqlglot (regex działa tylko gdy sqlglot nic nie zwróci) i nie zaniża istniejącej listy kolumn.
- Testy: uruchomione `pytest -q` (7 faili, 157 passed, 2 skipped) — regresje w `test_trialbalance_regression.py` jak wcześniej, liczba faili spadła o 1.
- Sprawdzenie tempów: ponowna analiza `update_stage_mis_LeadTime` pokazuje braki w wielu tempach (m.in. `#LeadTime_STEP1` 21/51, `#ContractInformationReference` 1/17, `#maxleaddate` 1/5, `#Offer_LON` 1/3) oraz pojawiające się `*` w schema dla `#offer`, `#maxcasenumber`, `#LeadTime_STEP2/3/4`.
- Problem otwarty: `LeadTime_STEP4` nie ma już `field: "*"`; kolumny wyliczane mają puste inputFields (UNKNOWN).

## Co zostało wykonane
- Zmiana w `engine.py`: gdy temp lineage ma `column_name="*"`, a kolumna istnieje w temp source, następuje mapowanie do konkretnej kolumny.
- Dostosowano mapowanie, by korzystało z per‑file i globalnego `temp_registry` (owner::#tmp), a nie z wyczyszczonego `parser.temp_registry`.
- Dodatkowo: jeśli wildcard `*` wskazuje na temp source bez danej kolumny, referencja jest odrzucana (unikamy `*` w wynikach).
- Dodano test regresyjny dla `LeadTime_STEP4` w `tests/test_leadtime_regression.py` (wymusza mapowanie kolumn temp→temp bez `*`).
- Uruchomiono testy: `pytest -q` (fail: 7/166, szczegóły w `test_trialbalance_regression.py`).
- Zweryfikowano artefakt `leadtime_check` → `LeadTime_STEP4` bez `field: "*"` (kolumny wyliczane mają puste inputFields).
- Utworzono narzędzie diagnostyczne `analyze_temp_procedure.py` i użyto go do sprawdzenia propagacji `SELECT *` między tempami w `update_stage_mis_LeadTime`.
- Rozszerzono analizator o porównanie listy kolumn z `SELECT INTO` (sqlglot) vs schema tempów; wykryto braki m.in. w `#LeadTime_STEP1`, `#LeadTime_STEP2`, `#LeadTime_STEP3`.
- W fallbacku parsera procedur dodano próbę sqlglot‑owej ekstrakcji projekcji dla `SELECT ... INTO` (przed regexem), aby uzupełnić kolumny tempów przy złożonych wyrażeniach.
- Fallback `SELECT ... INTO` nie nadpisuje już wyników z sqlglot i nie skraca istniejącej listy kolumn.
- Dodano test `test_procedure_select_into_fallback.py` (weryfikuje, że alias z wieloliniowego `CASE ... END` w `SELECT INTO` trafia do temp schema).

## Co jeszcze można spróbować
- Zidentyfikować, dlaczego mapowanie w `engine.py` nie zadziałało: prawdopodobnie brak dostępu do `temp_registry` w fazie 3 (stąd brak nazw kolumn dla temp źródeł).
- Rozważyć przeniesienie/serializację `temp_registry` do globalnego kontekstu (analogicznie do `global_saved_temp_sources`) i użyć go do mapowania `*`.
- Jeśli nadal są `*`, wzmocnić rejestrację kolumn w temp tables w fallbackach parsera (szczególnie dla `SELECT INTO`).
- Po zmianie w fallbacku uruchomić ekstrakcję dla `update_stage_mis_LeadTime` (odświeżyć `build/output/leadtime_check`) i ponownie porównać brakujące kolumny.
- Sprawdzić, dlaczego w outputach tempów pojawia się `*` (szczególnie `#offer`, `#maxcasenumber`, `#LeadTime_STEP2/3/4`) — upewnić się, że `_infer_table_columns_unified` zwraca kolumny i nie wstawia `*` jako placeholdera.
- Dodać test regresyjny w `tests/test_*.py` z minimalnym `SELECT INTO #tmp` i późniejszym użyciem `#tmp`, wymagający mapowania kolumna→kolumna.
- Jeśli puste inputFields dla kolumn wyliczanych są nieakceptowalne, spróbować poprawić lineage dla SELECT * + CASE (wyodrębnianie referencji z ekspresji).
- Skupić się na parserze `SELECT INTO` w procedurach: poprawić ekstrakcję kolumn (szczególnie gdy są złożone CASE/COALESCE/aliasy), bo temp schematy tracą atrybuty.

## Notatki techniczne

### Kluczowe moduły
- `engine.py`: Main extraction pipeline (3 phases)
- `lineage.py`: OpenLineage JSON generation
- `parser_modules/names.py`: Table name qualification
- `parser_modules/deps.py`: Dependency extraction

### Konwencje testowe
- Exclude: `test_trialbalance`, `test_temp_table_scoping`
- Run: `pytest -q tests/ -k "not trialbalance and not temp_table_scoping"`
- Regression: Dodać test do `tests/test_*.py` dla każdego fix

### Git workflow
- Branch: `dev`
- Commit format: `feat(module): description` lub `fix(module): description`
- Test przed commit: `pytest -q`
