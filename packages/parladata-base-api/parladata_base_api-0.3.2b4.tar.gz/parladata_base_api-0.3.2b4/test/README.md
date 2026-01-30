# Parladata Base API - Test Suite

Testni sistem za preverjanje delovanja Parladata Base API, s poudarkom na testiranju upravljanja članstev (memberships).

## Struktura Testnih Podatkov

### Organizacijska Hierarhija

```
Parliament of Test Country (root)
└── National Assembly (house) - glavna organizacija
    ├── Progressive Party Group (pg) - 5 članov
    ├── Conservative Alliance (pg) - 4 člani
    └── Green Movement (pg) - 1 član
```

### Dodatne Organizacije
- Committee on Finance (committee)
- Committee on Health (committee)

### Člani Parlamenta (10 članov)

**Progressive Party Group (5):**
- Anna Novak (president)
- Boris Kovač (deputy)
- Cecilia Horvat (member)
- David Krajnc (member)
- Eva Zupan (member)

**Conservative Alliance (4):**
- Filip Mlakar (president)
- Greta Potočnik (deputy)
- Henrik Pavlič (member)
- Irena Golob (member)

**Green Movement (1):**
- Jana Vidmar (president)

## Struktura Članstev

### Person Memberships

Vsak poslanec ima **dva membershipa**:

1. **Party Membership** - članstvo v poslanski skupini
   - `organization`: ID poslanske skupine
   - `role`: president/deputy/member
   - `on_behalf_of`: None

2. **Voter Membership** - glasovalna pravica v glavni organizaciji
   - `organization`: ID glavne organizacije (National Assembly)
   - `role`: voter
   - `on_behalf_of`: ID poslanske skupine

**Primer:** Anna Novak ima:
```python
{
    "member": anna_id,
    "organization": progressive_party_id,
    "role": "president",
    "on_behalf_of": None
}
{
    "member": anna_id,
    "organization": national_assembly_id,
    "role": "voter",
    "on_behalf_of": progressive_party_id
}
```

### Organization Memberships

Hierarhija organizacij:
- National Assembly je član Parliament of Test Country
- Vse poslanske skupine so člani National Assembly

## Uporaba

### 1. Generiranje Testnih Podatkov

```python
from test.data import generate_test_data

# Generiraj testne podatke
test_data = generate_test_data()

# Dostop do podatkov
mandate = test_data["mandate"]
organizations = test_data["organizations"]
people = test_data["people"]
org_memberships = test_data["organization_memberships"]
person_memberships = test_data["person_memberships"]
```

### 2. Zagon Integracijskih Testov

```bash
cd test
python test_api_integration.py \
    --api-url "http://localhost:8000/v1" \
    --username "your_username" \
    --password "your_password"
```

### 3. Testiranje s Python Skriptami

```python
from parladata_base_api.storages.storage import DataStorage
from test.data import generate_test_data

# Generiraj podatke
test_data = generate_test_data()

# Inicializiraj storage
storage = DataStorage(
    mandate_id=1,
    mandate_start_time="2022-01-01",
    main_org_id=2,  # National Assembly ID
    api_url="http://localhost:8000/v1",
    api_auth_username="username",
    api_auth_password="password"
)

# Uporabi storage za delo s podatki
storage.membership_storage.load_data()
```

## Testni Scenariji

### Testiranje Osnovnih Funkcij

1. **Kreiranje podatkov preko API**
   - Kreiranje mandata
   - Kreiranje organizacij
   - Kreiranje oseb
   - Kreiranje organizacijskih članstev
   - Kreiranje osebnih članstev

2. **Nalaganje podatkov preko Storage**
   - Inicializacija DataStorage
   - Nalaganje členov preko membership_storage
   - Preverjanje aktivnih glasovalcev

3. **Testiranje Membership Processing**
   - Parsanje začasnih podatkov
   - Kreiranje novih članstev
   - Končanje starih članstev

### Testiranje Edge Cases

1. **Poslanci brez stranke** (on_behalf_of=None)
2. **Menjava stranke** (spreminjanje on_behalf_of)
3. **Spreminjanje vlog** (president → member)
4. **Več organizacij z voter membershipi** (committee memberships)

## Struktura Datotek

```
test/
├── data.py                      # Generator testnih podatkov
├── test_api_integration.py      # Integracijski testi
└── README.md                    # Ta dokument
```

## API Endpoints

Test uporablja naslednje API endpoints:

- `POST /mandates/` - Kreiranje mandata
- `POST /organizations/` - Kreiranje organizacije
- `POST /people/` - Kreiranje osebe
- `POST /organization-memberships/` - Kreiranje org. članstva
- `POST /person-memberships/` - Kreiranje osebnega članstva
- `GET /person-memberships/?mandate={id}` - Pridobivanje članstev

## Preverjanje Podatkov

Po uspešnem zagonu testov lahko preverite:

1. **Število kreiranih objektov**
   - 1 mandat
   - 7 organizacij (root, house, 3 PG, 2 committees)
   - 10 oseb
   - 4 organizacijska članstva
   - 20 osebnih članstev (10 party + 10 voter)

2. **Aktivni glasovalci**
   - V `active_voters` strukturi naj bo 10 voter članstev
   - Vsak član naj ima pravilno nastavljeno `on_behalf_of`

3. **Organizacijska hierarhija**
   - House je član Root
   - Vse PG so člani House

## Napredne Funkcije

### Custom Test Data

```python
from test.data import TestDataGenerator

# Ustvari generator s custom datumom
generator = TestDataGenerator(mandate_start_date="2023-01-01")

# Generiraj podatke
data = generator.generate_all()

# Prikaži povzetek
print(generator.get_summary())
```

### Debugging

```python
import logging

# Vklopi debug logging
logging.basicConfig(level=logging.DEBUG)

# Zaženi teste
from test.test_api_integration import ParladataAPITester
tester = ParladataAPITester(api_url, username, password)
tester.run_full_test()
```

## Troubleshooting

### Napaka: "Organization already exists"
- Testni podatki so že v bazi
- Lahko nadaljujete, obstoječi podatki bodo uporabljeni

### Napaka: "Connection refused"
- Preverite, da je API strežnik zagnan
- Preverite API URL in port

### Napaka: "Authentication failed"
- Preverite uporabniško ime in geslo
- Preverite, da ima uporabnik ustrezne pravice

## Prihodnje Izboljšave

- [ ] Dodaj testiranje committee memberships
- [ ] Dodaj testiranje spreminjanja strank
- [ ] Dodaj testiranje end_time logike
- [ ] Dodaj cleanup funkcijo za odstranjevanje testnih podatkov
- [ ] Dodaj unit teste za posamezne storage metode
- [ ] Dodaj mock API za teste brez povezave

## Vprašanja in Podpora

Za vprašanja in pomoč kontaktirajte razvijalca ali odprite issue v repozitoriju.
