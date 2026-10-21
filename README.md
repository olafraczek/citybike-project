## Pierwsze uruchomienie (krok po kroku)

Poniższe kroki wykonuje każda osoba na swoim komputerze. Komendy wpisujemy w terminalu
(PowerShell w VS Code), ZAWSZE w głównym folderze repozytorium.

### 0. Wymagane przed startem
- Konto na GitHubie i zaakceptowane zaproszenie do repozytorium
  (mail od GitHuba albo https://github.com/olafraczek/citybike-project/invitations).
- Zainstalowane: Git, Anaconda/Miniconda, VS Code.

### 1. Skonfiguruj Gita (jednorazowo na komputerze)

```
git config --global user.name "Imię Nazwisko"
git config --global user.email "mail-z-githuba@example.com"
```

### 2. Sklonuj repozytorium

```
git clone https://github.com/olafraczek/citybike-project.git
cd citybike-project
code .
```

Przy pierwszym połączeniu z GitHubem pojawi się okno logowania, wystarczy się zalogować.

### 3. Utwórz własną gałąź

Gałąź nazywamy swoim imieniem (np. `olaf`, `<imie>`). Tworzymy ją od aktualnego `main`:

```
git checkout main
git pull
git checkout -b <imie>
git push -u origin <imie>
```

Od tego momentu pracujemy WYŁĄCZNIE na swojej gałęzi.
Sprawdzenie, na jakiej gałęzi jesteśmy: `git branch` (gwiazdka przy aktywnej).

### 4. Utwórz środowisko Pythona

```
conda create -n citibike python=3.11 -y
conda activate citibike
pip install -r requirements.txt
```

W VS Code: Ctrl+Shift+P → "Python: Select Interpreter" → wybierz środowisko `citibike`.

### 5. Skonfiguruj dostęp do baz

```
copy .env.example .env
```

Uzupełnij plik `.env` własnymi danymi (hasła, adresy baz).
Plik `.env` jest w `.gitignore`, więc nie trafi do repozytorium. Nie wysyłamy go na GitHuba.

### 6. Pobierz dane

Dane są zbyt duże na Git, więc każda osoba pobiera je lokalnie:

```
python src/download_citibike.py
```

Skrypt wypisze listę plików i rozmiar, po czym poprosi o potwierdzenie (`t`).
Pobiera archiwa z lat 2021–2025, rozpakowuje je do `data/raw/` i usuwa ZIP-y.
Przerwane pobieranie można wznowić, uruchamiając skrypt ponownie.

## Codzienna praca w Git

Na początku pracy podciągamy zmiany z `main` do swojej gałęzi:

```
git checkout main
git pull
git checkout <moja-galaz>
git merge main
```

Zapis i wysłanie swoich zmian:

```
git add .
git commit -m "Krótki opis zmiany"
git push
```

Po skończeniu etapu: na GitHubie "Compare & pull request" → merge do `main`.
Potem lokalnie:

```
git checkout main
git pull
git checkout <moja-galaz>
git merge main
```

## Co robić, gdy pojawi się konflikt przy `git merge main`

1. Git wypisze pliki z konfliktem. Otwórz je w VS Code, wybierz właściwą wersję
   (przyciski "Accept Current / Incoming / Both").
2. Zapisz pliki, a następnie:

```
git add .
git commit -m "Rozwiązanie konfliktu z main"
```