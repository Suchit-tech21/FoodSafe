# FoodSafe — Hackathon Ready

**Evidence-Based Food Safety Intelligence & Prevention Platform**

> Don't trust the stars. Check the evidence.

FoodSafe is a hackathon prototype connecting consumers, food businesses and safety monitoring through trusted data, transparent risk indicators, evidence-backed complaint reporting, complaint prioritization and preventive inventory expiry management.

## Core features

- Consumer restaurant search by name or locality
- Safety Profile with deterministic, explainable risk indicator
- Trust / provenance layer: Official, Verified, External, User Reported, Unverified
- Evidence-backed complaint submission with safe image upload
- Complaint priority scoring and real Priority Queue integration
- Persistent SQLite database
- Food inventory tracking with expiry status
- Real Min Heap integration for earliest expiry
- Verified Visit using QR/location/timestamp/bill/OTP evidence signals
- Restaurant QR generation and browser QR scanning where supported
- Optional OCR workflow using local Tesseract OCR; Search and QR are fallbacks
- Browser notification alerts for expiry conditions where permission is granted
- Food Safety Monitoring Dashboard
- Python Data Structures used by the web backend
- Original C Data Structures retained for course/hackathon demonstration

## Data Structures

The web application meaningfully uses:

| Feature | Data Structure |
|---|---|
| Restaurant exact/partial lookup | Hash Table + Merge Sort |
| Restaurant record organization | Linked List integration layer |
| Earliest inventory expiry | Min Heap |
| Complaint ordering | Priority Queue |
| Ranking/search support | Merge Sort / Binary Search modules |

The C implementation contains Hash Table, Linked List, Min Heap, Priority Queue, searching and sorting implementations as well.

## Risk engine

The risk indicator is deterministic and explainable. It considers license compliance, inspection availability, confirmed violations, verified reports, pending reports, inventory incidents and recency. Public/user reports are not represented as official violations.

## Demo data

The bundled database is seeded automatically with prototype/curated records. It is not a claim of live government data. The core demo has no dependency on FSSAI, government APIs, Google APIs, OpenAI APIs or paid services.

## Windows installation

Requirements: **Python 3.12**.

```powershell
cd FoodSafe_HACKATHON_READY
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python backend\app.py
```

Open:

```text
http://127.0.0.1:5000
```

You can also run `run.bat` after Python is installed. The batch file creates a virtual environment when needed, installs dependencies and starts Flask.

## Optional OCR

The UI includes the PDF's Camera → OCR → Restaurant Name → Database workflow as an optional enhancement. The backend uses `pytesseract` when a local Tesseract executable is available. If it is not installed, FoodSafe reports that limitation instead of pretending OCR succeeded. Search and QR identification remain available.

## API

- `GET /api/health`
- `GET /api/restaurants?q=...`
- `GET /api/restaurants/<id>`
- `GET /api/restaurants/<id>/risk`
- `GET /api/restaurants/<id>/provenance`
- `GET /api/restaurants/<id>/qr`
- `GET /api/complaints`
- `POST /api/complaints`
- `GET /api/complaints/<id>/evidence`
- `GET /api/inventory`
- `GET /api/inventory/heap`
- `POST /api/inventory`
- `PATCH /api/inventory/<id>`
- `DELETE /api/inventory/<id>`
- `GET /api/visits`
- `POST /api/visits`
- `POST /api/visits/otp`
- `POST /api/ocr`
- `GET /api/admin/dashboard`

## Hackathon demo sequence

1. **Consumer:** search `Green Leaf` → open Food Safety Profile → show risk factors → show provenance.
2. **Complaint:** Report Issue → Green Leaf → Hygiene → severity 8 → evidence → submit → show complaint ID and priority.
3. **Verified Visit:** select Green Leaf → choose QR/location/timestamp/bill/OTP evidence → verify visit. Generate a restaurant QR and demonstrate scanner if browser support is available.
4. **Inventory:** show Milk/Paneer/Sauce → add an item → show expiry status → show **MIN HEAP → Earliest Expiry**.
5. **Admin:** open Food Safety Monitoring Dashboard → show statistics → show complaints ordered by Priority Queue → show inventory alerts.

## C Data Structures demonstration

From `C/`:

```text
cd C
gcc -Wall -Wextra -std=c11 -Iinclude src/*.c -o foodsafe
.\foodsafe
```

Run the C tests:

```text
gcc -Wall -Wextra -std=c11 -Iinclude src/complaint.c src/hash_table.c src/inventory.c src/linked_list.c src/min_heap.c src/priority_queue.c src/restaurant.c src/risk.c src/searching.c src/sorting.c src/storage.c tests/test_main.c -o foodsafe_tests
.\foodsafe_tests
```

## Automated Python DS tests

```powershell
python -m unittest discover -s tests -v
```

## Limitations

- This is a hackathon prototype using curated/demo data where live official integrations are unavailable.
- QR scanning depends on browser camera permission and `BarcodeDetector` support.
- OCR is optional and requires a local Tesseract OCR executable; the application does not falsely claim OCR success when it is unavailable.
- OTP is a local demo flow and intentionally does not send real SMS.
- Browser notifications require user permission and supported browser APIs.


## IEEE Alignment Update — v3

Implemented from the IEEE comparison/Updated Idea:
- Role-based authentication with protected Admin/Moderator dashboard.
- Admin login: `Suchit / Suchit@2107`.
- Restaurant Management demo login: `restaurant / FoodSafe@2107`; choose the restaurant to manage after opening the Restaurant Management Login page. This demo account is for prototype evaluation; the backend scopes stock access to the selected restaurant.
- Complaint moderation: PENDING → VERIFIED/REJECTED with reviewer, remarks and timestamp.
- Binary Search is exposed through `/api/restaurants/binary-search?q=...` and integrated into restaurant search.
- Reproducible benchmark module under `benchmarks/`.
- Formal Flask API test suite under `tests/test_api.py`.
- Existing risk formula, provenance layer, Min Heap, Priority Queue, Hash Table, Linked List, Merge Sort, Verified Visit and OCR flow were preserved.

### Run
Windows:
1. `python -m venv .venv`
2. `.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `python backend/app.py`
5. Open `http://127.0.0.1:5000`

### Admin / moderation
Open **Admin Dashboard**, then login:
- Admin: `admin` / `admin123`
- Moderator: `moderator` / `mod123`

Pending complaints now show **Verify** and **Reject** actions. Each review records reviewer identity and timestamp.

### IEEE benchmarks
From the project root:
`python benchmarks/benchmark_report.py`

This generates `benchmarks/benchmark_results.csv`.

### API tests
From the project root:
`pytest -q`

The test suite covers authentication, dashboard protection, restaurant search/risk/provenance, Binary Search, complaints, inventory, visits, OCR validation and moderation review access.


## Restaurant Management Workspace

The separate **Restaurant Management Login** is intended for restaurant workers. After logging in, staff can view stock and expiry status for the selected restaurant and add inventory records. The FoodSafe Officer/Admin dashboard remains separate and retains the cross-restaurant reports, risk monitoring, priority queue, and expiry alerts.

## Consumer Photo Search

Selecting a photo shows a thumbnail and filename. Find by Photo runs OCR on the sign/menu and presents ranked restaurant suggestions when text is ambiguous; the user can select the correct result. OCR requires Tesseract OCR to be installed locally.


## Restaurant Map (prototype addition)

The Consumer page now includes an interactive map for the 25 restaurants in the local SQLite database. It uses Leaflet and OpenStreetMap tiles, so no Google Maps API key or billing account is needed to display the map. Select a pin or directory entry to see a restaurant's FoodSafe risk score and an illustrative rating. **All displayed ratings are simulated prototype values; they are not real Google ratings or reviews.** The “Open in Google Maps” link opens a Google Maps search for the selected restaurant. Some entries without exact coordinates use approximate neighborhood pins and are labelled as approximate. An internet connection is needed to load the external map library and map tiles.
