# VERSIONS.md — Hitos de versión (avance y cumplimiento)

Eje **distinto** al de las fases de `IMPLEMENTATION.md`. Las **fases** entregan funcionalidades; las **versiones** miden la madurez de ejecución/despliegue: de correr local hasta publicar. Una versión se da por cumplida cuando pasa su *definición de hecho*.

**Estado:** ⬜ pendiente · 🟡 en progreso · ✅ cumplido

| Versión | Hito | Definición de hecho | Depende de | Estado |
|---|---|---|---|---|
| **v0.1** | Core local | La Core API corre con `uvicorn`; `pytest` (unit + componente) en verde; emuladores y `seed.py` cargan el caso del piloto; `/health` y `/simulate` responden. | Fase 0 + core de Fase 1 | ⬜ |
| **v0.2** | Web local | La web (Vite) consume la API local vía `api-client`; flujos núcleo visibles (plan, transacciones, comparativa). | v0.1 + Fase 1 web | ⬜ |
| **v0.3** | Mobile local | La app Expo consume la misma API local; paridad de pantallas núcleo. | v0.2 | ⬜ |
| **v0.4** | Deploy Dev | Core API en **Cloud Run** (proyecto `finanzas-dev`), Firestore real, web en **Firebase Hosting**, secretos en **Secret Manager**, service account con mínimo privilegio. | v0.2 | ⬜ |
| **v0.5** | IA + Background en Dev | Chat con streaming en dev; **Cloud Scheduler** dispara `/close-month` y `/alerts`; alertas proactivas funcionando. | v0.4 + Fase 2 (IA) | ⬜ |
| **v0.6** | Hardening | Checklist de seguridad completo (auth en API, reglas probadas con `rules-unit-testing`, CORS, rate limit, audit log, backups), monitoreo (Cloud Logging) y **CI/CD** (GitHub Actions). | v0.5 | ⬜ |
| **v1.0** | Publish | Proyecto `finanzas-prod`; web pública; mobile en TestFlight/Play (beta); alertas de billing; runbook de operación. Listo para usuarios reales más allá del piloto. | v0.6 + Fase 2 completa | ⬜ |
| **v1.x+** | Escala | Funcionalidades P2 (payoff, categorización, RAG, OCR, open banking) liberadas de forma incremental. | v1.0 + Fase 3 | ⬜ |

---

## Cómo usar este tracker
- Cada versión se cierra solo cuando **todas** las condiciones de su *definición de hecho* están listas — no por avance parcial.
- Mantener sincronía con `IMPLEMENTATION.md`: una versión suele requerir ciertas filas de fase completas.
- Registrar fecha y tag de git al cumplir cada versión (`v0.1`, `v0.2`, …) para medir ritmo real.
- **Local-first**: no saltar a v0.4 (deploy) sin v0.1–v0.3 en verde.
