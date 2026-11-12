# 🌾 HarvestLink AI



### Agentic AI-Powered Agricultural Commerce Platform



HarvestLink AI is an agricultural commerce platform designed to connect farmers, buyers, and FPO (Farmer Producer Organisation) operators through AI-assisted listing creation, intelligent matching, transparent order management, and digital payments.



The platform supports Tamil and English listing input, helping farmers communicate their available produce and connect with potential buyers.



## 🚀 Key Features



- **Tamil and English Listing Input:** Create agricultural listings using Tamil or English text and voice-oriented listing workflows.

- **AI-Assisted Parsing:** Extract crop names, quantities, prices, and locations from listing descriptions.

- **Multi-Agent Workflow:** Separate agent components support commerce, demand discovery, matching, and negotiation workflows.

- **Buyer-Farmer Matching:** Match farmer listings with buyer requirements.

- **Approval Workflow:** Support farmer and buyer approval or rejection of proposed matches.

- **Authentication:** Email/password and mobile OTP authentication endpoints.

- **Order Management:** Manage orders and delivery confirmation.

- **Digital Payments:** PayPal Sandbox integration with a mock payment mode for local demonstrations.

- **FPO Operator Support:** Operator listing workflows and audit logs.

- **Impact Monitoring:** Dashboard metrics and agent activity logs.



## 🛠️ Technology Stack



| Layer | Technologies |

|---|---|

| Frontend | React 19, Vite 6 |

| Styling | Tailwind CSS 3 |

| Backend | Python, FastAPI |

| Database | SQLite, SQLAlchemy |

| Data Validation | Pydantic |

| AI Workflow | LangGraph, LangChain Core |

| Configuration | Python Dotenv |

| API Server | Uvicorn |

| Payments | PayPal Sandbox |



## 🏗️ Project Architecture



```text

HarvestLink-AI/

│

├── backend/

│   ├── app/

│   │   ├── agents/

│   │   │   ├── commerce_agent.py

│   │   │   ├── demand_discovery.py

│   │   │   ├── matching_agent.py

│   │   │   ├── negotiation_agent.py

│   │   │   ├── llm_client.py

│   │   │   ├── state.py

│   │   │   └── workflow.py

│   │   │

│   │   ├── api/

│   │   │   ├── auth.py

│   │   │   ├── listings.py

│   │   │   ├── buyers.py

│   │   │   ├── matching.py

│   │   │   ├── orders.py

│   │   │   ├── payments.py

│   │   │   ├── operator.py

│   │   │   ├── impact.py

│   │   │   ├── logs.py

│   │   │   └── demo.py

│   │   │

│   │   ├── core/

│   │   │   ├── config.py

│   │   │   ├── geo.py

│   │   │   └── security.py

│   │   │

│   │   ├── database/

│   │   ├── models/

│   │   ├── schemas/

│   │   ├── services/

│   │   │   ├── tamil_parser.py

│   │   │   ├── matching_service.py

│   │   │   ├── order_service.py

│   │   │   ├── inventory_service.py

│   │   │   ├── otp_service.py

│   │   │   └── paypal_service.py

│   │   │

│   │   └── main.py

│   │

│   └── tests/

│

├── frontend/

│   ├── src/

│   │   ├── App.jsx

│   │   ├── api.js

│   │   ├── i18n.js

│   │   ├── index.css

│   │   └── main.jsx

│   ├── package.json

│   └── vite.config.js

│

├── scripts/

├── requirements.txt

├── .env.example

├── .gitignore

└── README.md

```



## ⚙️ Local Installation and Setup



### Prerequisites



Install the following:



- Python 3.10 or later

- Node.js and npm

- Git



### 1. Clone the repository



```bash

git clone https://github.com/rakshithamit25-cloud/HarvestLink-AI.git

cd HarvestLink-AI

```



### 2. Set up the Python backend



Create and activate a virtual environment.



**Windows PowerShell:**



```powershell

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

```



Install backend dependencies:



```powershell

python -m pip install -r requirements.txt

```



### 3. Configure environment variables



Create your local environment file:



```powershell

Copy-Item .env.example .env

```



Review `.env` and configure your own values.



Important settings:



| Variable | Description |

|---|---|

| `ENVIRONMENT` | Application environment |

| `SECRET_KEY` | Application security key |

| `DATABASE_URL` | Database connection |

| `DEMO_MODE` | Enables demo API endpoints |

| `OTP_DEMO_MODE` | Enables demo OTP behavior |

| `LLM_PROVIDER` | AI provider selection |

| `LLM_API_KEY` | AI provider API key |

| `LLM_MODEL` | Selected model |

| `LLM_BASE_URL` | AI provider endpoint |

| `PAYPAL_MODE` | `mock` or `sandbox` |

| `PAYPAL_CLIENT_ID` | PayPal Sandbox client ID |

| `PAYPAL_CLIENT_SECRET` | PayPal Sandbox secret |

| `PAYPAL_CURRENCY` | Payment currency |

| `FRONTEND_URL` | Allowed frontend origins |

| `BACKEND_URL` | Backend URL |



The provided `.env.example` is configured for local development and demo mode.



For local testing, the heuristic AI provider and mock payment mode can be used without external API credentials.



For actual PayPal Sandbox integration, configure your own Sandbox credentials.



**Never commit your `.env` file or expose API keys and payment credentials.**



### 4. Start the backend



From the project root:



```powershell

.\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --app-dir backend

```



Backend URL:



```text

http://localhost:8000

```



Interactive API documentation:



```text

http://localhost:8000/docs

```



Health endpoint:



```text

http://localhost:8000/api/health

```



On startup, the application initializes database tables and seeds demo data.



### 5. Install and start the frontend



Open a second terminal:



```powershell

cd frontend

npm install

npm run dev

```



Open the frontend in your browser:



```text

http://localhost:5173

```



### 6. Build the frontend



To create a production frontend build:



```powershell

cd frontend

npm run build

```



The generated build is placed in `frontend/dist`.



## 🔄 Application Workflow



1. **Farmer Listing:** A farmer enters crop details, quantity, expected price, and location using Tamil or English input.

2. **Information Extraction:** The backend parser extracts relevant listing information.

3. **Buyer Requirements:** Buyers submit their agricultural product requirements.

4. **AI-Assisted Matching:** Matching components evaluate available listings against buyer requirements.

5. **Approval:** Farmers and buyers can approve or reject proposed matches.

6. **Order Creation:** Approved matches can proceed through the order workflow.

7. **Payment:** Payment processing uses the configured mock or PayPal Sandbox mode.

8. **Monitoring:** Agent logs, operator audit logs, and impact metrics support activity monitoring.



## 🔌 API Overview



The backend provides REST API endpoints through FastAPI.



| Module | Example endpoint |

|---|---|

| Health | `GET /api/health` |

| Authentication | `/api/auth/` |

| OTP Authentication | `/api/auth/otp/` |

| Listings | `/api/listings` |

| Listing Text Parsing | `POST /api/listings/parse-text` |

| Buyer Requirements | `/api/buyers/requirements` |

| Matching | `/api/matching/` |

| Orders | `/api/orders` |

| Payments | `/api/payments/` |

| Operator | `/api/operator/` |

| Impact Metrics | `/api/impact/metrics` |

| Agent Logs | `/api/logs/agent` |

| Demo | `/api/demo/` |



For complete request and response schemas, visit:



`http://localhost:8000/docs`



## 🧪 Testing



Run the backend test suite from the project root:



```powershell

python -m pytest backend/tests/ -v

```



The project test suite has previously passed **77 tests**.



## 💳 Payment Configuration



HarvestLink AI supports two payment modes:



- **Mock mode:** Simulates payment processing for local demonstrations.

- **PayPal Sandbox mode:** Uses configured PayPal Sandbox credentials for testing the payment workflow.



The current demonstration configuration uses USD for PayPal Sandbox payments. Spoken INR prices are not automatically converted to USD.



Sandbox transactions are for testing and do not represent real production payments.



## 🔐 Security and Deployment Notes



- Keep `.env` and private credentials out of version control.

- Replace development secrets before production deployment.

- Use a production database configuration where appropriate.

- Configure frontend origins correctly for deployment.

- Use HTTPS and production-grade authentication and payment settings.

- Validate external AI and payment service configuration before enabling production workflows.



The frontend currently uses `http://localhost:8000/api` as its API base URL. Update the frontend API configuration when deploying to a different backend address.



## 🌱 Future Improvements



- More robust regional-language speech recognition.

- Improved crop and quantity extraction for different dialects.

- Advanced demand forecasting and price intelligence.

- More detailed geographic farmer-buyer matching.

- Production deployment with scalable database infrastructure.

- Expanded farmer accessibility and offline support.



## 🎯 Project Vision



Our vision is to make agricultural commerce more accessible, transparent, and efficient by helping farmers connect directly with buyers through intelligent digital tools.



**HarvestLink AI — Connecting Farmers, Buyers, and Opportunities.**



---



**Repository:** https://github.com/rakshithamit25-cloud/HarvestLink-AI                                                                       ## ⚠️ Limitations (Honest Status)



- **PayPal:** Verified with a real Sandbox payment. Use US-based Sandbox accounts (India-based ones fail with a currency error). Prices are in USD; spoken rupee prices are not converted.

- **Mobile OTP login:** Verification logic is implemented, but delivery is in demo mode (the code is shown on screen). SMS delivery is future work.

- **Reservation expiry:** Not implemented; stock is released on rejection only.

- **Database:** PostgreSQL is untested; SQLite is the tested database.

- **Operator dashboard:** Operators currently see an empty order list.

- **Voice input and audio playback:** Tested in Chrome only.

- **AI agents:** Call a Groq LLM when an API key is configured; otherwise, they use rule-based processing. The Agent Activity Panel shows which mode ran.



## License



MIT



