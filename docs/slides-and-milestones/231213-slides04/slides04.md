
# Postępy prac

## Prace wykonane na rzecz projektu w okresie od ostatniego spotkania
   
1. Finalizacja prac nad modelem formalnym
2. Stworzenie dokumentu z opisem modelu formalnego
3. Rozpoczęcie implementacji modelu formalnego
4. Implementacja GUI symulatora
  
## Zestawienie osób i wykonanych przez nie zadań

+---------------------------------------------------+-----------+-----------+-----------+
| Zadanie                                           | Łukasz \  | Dawid \   | Mateusz \ |
|                                                   | Łabuz     | Małecki   | Mazur     |
+:==================================================+:=========:+:=========:+:=========:+
| Finalizacja prac nad modelem formalnym            |\checkmark |\checkmark |\checkmark |
+---------------------------------------------------+-----------+-----------+-----------+
| Stworzenie dokumentu z opisem modelu formalnego   |           |           |\checkmark |
+---------------------------------------------------+-----------+-----------+-----------+
| Rozpoczęcie implementacji modelu formalnego       |\checkmark |\checkmark |\checkmark |
+---------------------------------------------------+-----------+-----------+-----------+
| Implementacja GUI symulatora                      |           |           |\checkmark |
+---------------------------------------------------+-----------+-----------+-----------+

# Model formalny

## Przypomnienie celu projektu

Celem projektu jest stworzenie modelu symulacyjnego ruchu drogowego na rondzie Grunwaldzkim w krakowie.

![Obszar symulacji. Źródło: Google My Maps](img/obszar-symulacji.png){height=60%}

## Materiały źródłowe

Kwerenda literaturowa naszego projektu została podzielona na dwie sekcje - główną oraz pomocniczą.

Materiały z sekcji głównej stanowią podstawę naszego modelu formalnego,
natomiast materiały z sekcji pomocniczej są dodatkowymi źródłami informacji,
które mogą okazać się przydatne w trakcie jego implementacji.   

### Główne materiały źródłowe

- Gora P. *Adaptacyjne planowanie ruchu drogowego* [@gora2010adaptacyjne]
- Rasouli A. *Pedestrian Simulation: A Review* [@rasouli2021pedestrian]

## Skale oraz technika symulacji

W materiale [@rasouli2021pedestrian] przedstawione zostały definicje różnych skal oraz technik symulacji.

W naszym projekcie wykorzystujemy następujące:

### Techniki symulacji

**Model komórkowy** - model polegający na dyskretyzacji obszarów, na których poruszają się symulowane jednostki. Według założenia, każda z nich może zajmować jedną komórkę na siatce w danym momencie. W każdym kroku symulacji, jednostki mogą zmienić swoją pozycję na sąsiednią komórkę.

---

### Skale symulacji

**Agent-Based** - skala, w której każda jednostka jest rozróżnialna, ma własne, zdefiniowane statystyki oraz zbiór możliwych do podjęcia decyzji. Na jej zachowanie ma wpływ otoczenie, infrastruktura czy też inne jednostki.

**Entity-Based** - skala, w której jednostki są z założenia nierozróżnialne. Nie wyróżniają się niczym. Zachowują się według ściśle ustalonych reguł. Nie mają wpływu na otoczenie. 

## Elementy modelu formalnego

### Automat komórkowy

W naszym modelu formalnym wykorzystujemy definicję automatu komórkowego przedstawioną w [@gora2010adaptacyjne] - rysunek \ref{img_gora_2009_def_aut_kom}.

---

![Definicja Automatu komórkowego przedstawiona w [@gora2010adaptacyjne] \label{img_gora_2009_def_aut_kom}](img/gora-2010-definicja-automatu-komorkowego.png)

---

### Jednostki

Algorytmy zachowania jednostek, które wchodzą w skład naszego modelu, przedstawiają następujące rysunki:

- pojazdy - rysunek \ref{img_gora_2009_alg_ruch_poj}
- piesi - rysunek \ref{img_rasouli_2021_alg_ruch_piesz}
- sygnalizacja świetlna - rysunek \ref{img_gora_2009_akg_sygn_sw}.

---

![Algorytm ruchu pojazdów przedstawiony w [@gora2010adaptacyjne] \label{img_gora_2009_alg_ruch_poj}](img/gora-2010-alg-ruch-poj.png)

---

![Algorytm ruchu pieszych przedstawiony w [@rasouli2021pedestrian] \label{img_rasouli_2021_alg_ruch_piesz}](img/rasouli-2021-alg-ruch-piesz.png){height=80%}

---

![Algorytm działania sygnalizacji świetlnej przedstawiony w [@gora2010adaptacyjne] \label{img_gora_2009_akg_sygn_sw}](img/gora-2010-akg-sygn-sw.png)

## Podsumowanie

Praca [@gora2010adaptacyjne], oprócz wyżej wymienionych definicji i algorytmów (Rysunki \ref{img_gora_2009_def_aut_kom}, \ref{img_gora_2009_alg_ruch_poj}, \ref{img_gora_2009_akg_sygn_sw}),
zawiera również szerokie opisy poszczególnych elementów modelu oraz ich zachowań. 

Praca [@rasouli2021pedestrian] zawiera krótki, ale konkretny opis algorytmu ruchu pieszych
oraz ich zachowania.

Na bazie tych materiałów, stworzyliśmy model formalny, który posłuży nam jako podstawa implementacji symulatora.

---

### Model formalny

Nasz model jest połączeniem elementów z obu prac.

\
Dzięki obszernym opisom z pracy [@gora2010adaptacyjne] łatwo było nam zrozumieć, jak poszczególne elementy modelu powinny ze sobą współpracować oraz jak, do modelu przedstawionego przez jego autora, dodać symulację pieszych z pracy [@rasouli2021pedestrian]. 

\
Stworzenie aplikacji symulacyjnej na podstawie tak przygotowanego modelu nie powinno zatem stanowić problemu.
Potwierdzają to dotychczasowe postępy prac.

# Implementacja symulatora

## Minione zadanie - Próba implementacji prostego modelu NaSch

Jakiś czas temu postanowiliśmy spróbować zaimplementować prosty model NaSch, 
aby lepiej zapoznać się z biblioteką *CellPyLib* oraz problematyką projektu.

Wyniki zadania pokazały, że implementacja modelu NaSch nie jest trudna, 
ale biblioteka *CellPyLib* nie nadaje się idealnie do implementacji tego typu modelu. 

Po dalszej analizie zdecydowaliśmy się zrezygnować z biblioteki *CellPyLib* i zaimplementować model samodzielnie.

## Aktualny stan prac

W trakcie ostatnich dwóch tygodni udało nam się zaimplementować podstawowe elementy składowe modelu formalnego.

Naszą uwagę skupiliśmy głównie na implementacji GIU symulatora, aby móc w łatwy sposób testować działanie naszego modelu.

### GUI symulatora

Nowe GUI symulatora zostało wykorzystuje o bibliotekę *Pygame*.

\
Umożliwia ono wyświetlanie stanu symulatora w czasie rzeczywistym.
Możliwe jest przybliżanie (klawisze *z*,*c*) i przesuwanie widoku widoku (*strzałki*). Obecny wygląd GUI symulatora przedstawiają 
rysunki \ref{img_gui_symulatora_1} oraz \ref{img_gui_symulatora_2}.

---

![GUI symulatora - widok ogólny. Dla zwiększenie czytelności graf dróg jest nanoszony na obraz z map (źródło: [OpenStreetMap](openstreetmap.org)). Wierzchołki grafu (skrzyżowania) przedstawione są jako szare punkty. Krawędzie składają się z co najmniej jednej, kropkowanej linii. Linie obrazują pasy ruchu, a kropki komórki automatu. \label{img_gui_symulatora_1}](img/simulator-gui-1.png)

---

![GUI symulatora - widok przybliżony. Dla zwiększenie czytelności graf dróg jest nanoszony na obraz z map (źródło: [OpenStreetMap](openstreetmap.org)). Wierzchołki grafu (skrzyżowania) przedstawione są jako szare punkty. Krawędzie składają się z co najmniej jednej, kropkowanej linii. Linie obrazują pasy ruchu, a kropki komórki automatu. \label{img_gui_symulatora_2}](img/simulator-gui-2.png)


# Pytania

# Dziękujemy za uwagę

# Bibliografia
