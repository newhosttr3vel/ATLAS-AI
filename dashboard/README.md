# ATLAS AI Control Center

The Streamlit UI is the human-facing workspace for the prototype. It connects to the FastAPI service and provides:

- Overview dashboard and KPIs
- Lead creation and search
- Sales task creation, review, JSON editing, approval, and rejection
- AI team structure and assignment activity
- Weekly performance summary
- Arabic-first UI with English language toggle

## Run inside GitHub Codespaces

Start FastAPI in one terminal:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Start the dashboard in a second terminal:

```bash
python -m streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501
```

Open forwarded port **8501** from the Codespaces Ports panel.

The dashboard uses `ATLAS_API_URL` (default: `http://127.0.0.1:8000`) and the `X-Agency-ID` header. This agency selector is only a prototype partition key, not authentication or authorization.

All agent outputs are deterministic mock results. No booking, supplier availability, live price, payment, or customer communication is performed.
