---
title: Symulacja ruchu drogowego na przykładzie ronda Grunwaldzkiego w Krakowie
subtitle: |
    Projekt zespołu 05 na przedmiot \
    *Symulacja Systemów Dyskretnych*
author: |
    Łukasz Łabuz \
    Dawid Małecki \
    Mateusz Mazur
header-includes:
    - \usetheme {Antibes}
---

# Plan projektu 

## Planowany harmonogram prac nad projektem

**19.10.2023** - Stworzenie podstawowego opisu podstawowych założeń projektu i wybranego modelu, harmonogramu i podziału zadań

**02.11.2023** - Przygotowanie kwerendy literaturowej dotyczącej metod poruszanych w projekcie

**30.11.2023** - Przygotowanie pełnego modelu formalnego, który zostanie wykorzystany podczas implementacji rozwiązania przedstawionego problemu

**14.12.2023** - Przedstawienie gotowego prototypu symulacji

**25.01.2024** - Prezentacja skończonego projektu

## Wstępny podział zadań

+---------------------------------------+-----------+-----------+-----------+
| Zadanie                               | Łukasz \  | Dawid \   | Mateusz \ |
|                                       | Łabuz     | Małecki   | Mazur     |
+:======================================+:=========:+:=========:+:=========:+
| Wybranie stosu technologicznego       |\checkmark |\checkmark |\checkmark |
| dla projektu                          |           |           |           |
+---------------------------------------+-----------+-----------+-----------+
| Ustalenie zakresu symulacji           |\checkmark |\checkmark |\checkmark |
+---------------------------------------+-----------+-----------+-----------+
| Wyszukiwanie kwerendy literaturowej   |\checkmark |\checkmark |\checkmark |
+---------------------------------------+-----------+-----------+-----------+
| Stworzenie modelu formalnego          |\checkmark |\checkmark |\checkmark |
+---------------------------------------+-----------+-----------+-----------+
| Koordynacja repozytorium projektu     |           |\checkmark |           |
+---------------------------------------+-----------+-----------+-----------+
| Implementacja algorytmów              |\checkmark |\checkmark |\checkmark |
+---------------------------------------+-----------+-----------+-----------+
| Stworzenie dokumentacji               |           |           |\checkmark |
+---------------------------------------+-----------+-----------+-----------+

## Zakres symulacji

### Obszar symulacji

Rondo Grunwaldzkie w Krakowie z najbliższymi dochodzącymi ulicami

![Obszar symulacji (zaznaczony na niebiesko)](img/obszar-symulacji.png){width=50%}

----

### Elementy symulacji

- Samochody
- Piesi
- Sygnalizacja świetlna
- Komunikacja miejska (ewentualnie)

## Wstępne założenia techniczne co do technologii.

**Język:** Python

**Biblioteki:**

- [NumPy](https://numpy.org/)
- [MatPlotLib](https://matplotlib.org/)
- [CellPyLib](https://pypi.org/project/cellpylib/)

# Wstępna kwerenda literaturowa

## Paweł Gora *Adaptacyjne planowanie ruchu drogowego*

W pracy przedstawione zostały metody adaptacyjnego planowania ruchu drogowego oparte na algorytmie genetycznym. Ich skuteczność przetestowana została przy użyciu **symulatora ruchu drogowego TSF** (Traffic Simulation Framework). Opisana została również architektura samego symulatora oraz techniczne aspekty jego implementacji przy u˙zyciu technologii .NET Framework

## Amir Rasouli *Pedestrian Simulation: A Review*

Artykuł ten skupia się na różnych aspektach modelu ruchu pieszego (tłumu) –
i symulacji. Przegląd obejmuje: różne kryteria modelowania, m.in jak szczegółowość, techniki i czynniki zaangażowane w modelowanie zachowań pieszych zachowanie i różne metody symulacji pieszych z bardziej szczegółowymi wynikami przyjrzyjmy się dwóm sposobom symulowania zachowań pieszych w scenach ruchu drogowego. Na koniec przedstawiono zalety i wady różnych technik symulacyjnych omówiono i sformułowano zalecenia dotyczące przyszłych badań.

# Postępy prac

## Prace wykonane na rzecz projektu w okresie od ostatniego spotkania

1. Ustalenie harmonogramu prac nad projektem
2. Ustalenie wstępnego podziału zadań
3. Ustalenie zakresu symulacji
4. Wyszukiwanie kwerendy literaturowej
  
## Zestawienie osób i wykonanych przez nie zadań

+---------------------------------------+-----------+-----------+-----------+
| Zadanie                               | Łukasz \  | Dawid \   | Mateusz \ |
|                                       | Łabuz     | Małecki   | Mazur     |
+:======================================+:=========:+:=========:+:=========:+
| Wybranie stosu technologicznego       |\checkmark |\checkmark |\checkmark |
| dla projektu                          |           |           |           |
+---------------------------------------+-----------+-----------+-----------+
| Ustalenie zakresu symulacji           |\checkmark |\checkmark |\checkmark |
+---------------------------------------+-----------+-----------+-----------+
| Wyszukiwanie kwerendy literaturowej   |\checkmark |\checkmark |\checkmark |
+---------------------------------------+-----------+-----------+-----------+
| Koordynacja repozytorium projektu     |           |\checkmark |           |
+---------------------------------------+-----------+-----------+-----------+

# Dziękujemy za uwagę
