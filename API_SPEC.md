# Finanzly – Especificación de API

**Base URL producción:** `https://sistema-finanzas-personales.up.railway.app`
**Base URL local:** `http://localhost:8000`

---

## Convenciones generales

| Aspecto | Detalle |
|---|---|
| Autenticación | `Authorization: Bearer <token>` en el header |
| Formato | JSON en request y response (`Content-Type: application/json`) |
| Fechas | `YYYY-MM-DD` |
| Montos | Siempre positivos — el tipo `ingreso`/`gasto` define el signo |
| Errores | Siempre `{ "message": "descripción" }` con el HTTP status correspondiente |

---

## Configuración de Postman

### 1. Crear environment `Finanzly`

| Variable | Valor inicial |
|---|---|
| `baseUrl` | `https://sistema-finanzas-personales.up.railway.app` |
| `token` | *(vacío — se llena automáticamente)* |

### 2. Script para guardar el token automáticamente

Pegar esto en la pestaña **Tests** de los requests de **register** y **login**:

```javascript
const json = pm.response.json();
if (json.token) {
    pm.environment.set("token", json.token);
    console.log("✅ Token guardado");
}
```

### 3. Usar el token en requests privados

En la pestaña **Authorization** de cada request:
- Type: `Bearer Token`
- Token: `{{token}}`

---

## 1. AUTH

### POST /auth/register

No requiere autenticación.

**Body:**
```json
{
    "name": "Juan Pérez",
    "email": "juan@correo.com",
    "password": "minimo6"
}
```

**Respuesta `201`:**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": 1,
        "name": "Juan Pérez",
        "email": "juan@correo.com"
    }
}
```

**Errores:**
| Status | Mensaje |
|---|---|
| `400` | `"Este email ya está registrado"` |

---

### POST /auth/login

No requiere autenticación.

**Body:**
```json
{
    "email": "juan@correo.com",
    "password": "minimo6"
}
```

**Respuesta `200`:**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": 1,
        "name": "Juan Pérez",
        "email": "juan@correo.com"
    }
}
```

**Errores:**
| Status | Mensaje |
|---|---|
| `401` | `"Credenciales incorrectas"` |

---

### GET /auth/me

Devuelve el usuario autenticado. El frontend lo usa para saber si mostrar el onboarding.

**Auth:** Requerida

**Respuesta `200`:**
```json
{
    "id": 1,
    "name": "Juan Pérez",
    "email": "juan@correo.com",
    "onboardingCompleted": false
}
```

> Si `onboardingCompleted` es `false`, redirigir al wizard de configuración inicial.

---

### POST /auth/logout

**Body:** vacío

**Respuesta `200`:**
```json
{ "message": "Sesión cerrada correctamente" }
```

---

### POST /api/token/refresh/

Renueva el access token. El refresh token se lee automáticamente de la cookie.
Usado por el interceptor de Axios.

**Body:** vacío

**Respuesta `200`:** Setea nueva cookie. Body vacío `{}`.

**Errores:**
| Status | Detalle |
|---|---|
| `401` | `"Sesión expirada"` |

---

## 2. ONBOARDING

### POST /onboarding

Se llama **una sola vez** al terminar el wizard. Guarda el ingreso mensual y crea los presupuestos iniciales.

**Auth:** Requerida

**Body:**
```json
{
    "monthlyIncome": 15000,
    "categories": [
        { "label": "Vivienda",     "budgetLimit": 5000 },
        { "label": "Alimentación", "budgetLimit": 3000 },
        { "label": "Transporte",   "budgetLimit": 1500 },
        { "label": "Ocio",         "budgetLimit": 1000 }
    ]
}
```

**Respuesta `204`:** Sin cuerpo.

> Después de este request, `GET /auth/me` devolverá `onboardingCompleted: true`.

---

## 3. TRANSACCIONES

### GET /transactions

Devuelve todas las transacciones del usuario, ordenadas por fecha descendente.

**Auth:** Requerida

**Respuesta `200`:**
```json
[
    {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "desc": "Sueldo abril",
        "amount": 15000.0,
        "type": "ingreso",
        "category": "Otros",
        "date": "2026-04-01"
    },
    {
        "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "desc": "Supermercado",
        "amount": 850.0,
        "type": "gasto",
        "category": "Alimentación",
        "date": "2026-04-10"
    }
]
```

---

### POST /transactions

**Auth:** Requerida

**Body — ingreso:**
```json
{
    "desc": "Sueldo",
    "amount": 15000.00,
    "type": "ingreso",
    "category": "Otros",
    "date": "2026-04-01"
}
```

**Body — gasto:**
```json
{
    "desc": "Gasolinera",
    "amount": 800.00,
    "type": "gasto",
    "category": "Transporte",
    "date": "2026-04-12"
}
```

**Respuesta `201`:**
```json
{
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "desc": "Gasolinera",
    "amount": 800.0,
    "type": "gasto",
    "category": "Transporte",
    "date": "2026-04-12"
}
```

**Errores:**
| Status | Mensaje |
|---|---|
| `400` | `"type debe ser \"ingreso\" o \"gasto\""` |
| `400` | `"amount debe ser un número positivo"` |
| `400` | `"date debe tener formato YYYY-MM-DD"` |

---

### GET /transactions/summary

Resumen del mes activo (calculado según el `monthStartDay` del usuario).

**Auth:** Requerida

**Respuesta `200`:**
```json
{
    "ingresos": 15000.0,
    "gastos": 8500.0,
    "balance": 6500.0
}
```

---

### GET /transactions/categories

Distribución porcentual de gastos por categoría en el mes activo. Usado para la gráfica de pastel.

**Auth:** Requerida

**Respuesta `200`:**
```json
[
    { "label": "Vivienda",     "value": 45, "color": "#60a5fa" },
    { "label": "Alimentación", "value": 30, "color": "#34d399" },
    { "label": "Transporte",   "value": 25, "color": "#fbbf24" }
]
```

> `value` es porcentaje entero — todos suman 100. Si no hay gastos devuelve `[]`.

---

### POST /transactions/import

Importa transacciones desde un archivo CSV o Excel.

**Auth:** Requerida
**Content-Type:** `multipart/form-data`
**Campo:** `file` → archivo `.csv` o `.xlsx`

**Formato del CSV (columnas requeridas):**
```
desc,amount,type,category,date
Supermercado,850,gasto,Alimentación,2026-04-10
Sueldo,15000,ingreso,Otros,2026-04-01
Gasolinera,600,gasto,Transporte,2026-04-08
```

**Respuesta `200`:**
```json
{ "imported": 3 }
```

**Cómo probarlo en Postman:**
1. Method `POST` → URL `{{baseUrl}}/transactions/import`
2. Body → `form-data`
3. Key: `file` → cambiar tipo a **File** → seleccionar el archivo

---

### GET /transactions/export

Descarga el historial. El token va como **query param** porque es descarga directa del navegador.

**Auth:** Token en query param (no en header)

**Parámetros:**
| Param | Valores | Requerido |
|---|---|---|
| `format` | `csv` o `pdf` | Sí |
| `token` | JWT del usuario | Sí |

**URLs de ejemplo:**
```
GET {{baseUrl}}/transactions/export?format=csv&token={{token}}
GET {{baseUrl}}/transactions/export?format=pdf&token={{token}}
```

**Respuesta:** Archivo descargable.

**Cómo probarlo en Postman:**
1. Method `GET` → URL `{{baseUrl}}/transactions/export`
2. Params → agregar `format=csv` y `token={{token}}`
3. Enviar → Body → `Save Response` → `Save to a file`

---

## 4. PRESUPUESTOS

### GET /budgets

Devuelve presupuestos con el gasto acumulado en el mes activo.

**Auth:** Requerida

**Respuesta `200`:**
```json
[
    {
        "id": "4a7b2c1d-1234-5678-abcd-ef0123456789",
        "label": "Vivienda",
        "icon": "🏠",
        "color": "#60a5fa",
        "limit": 5000.0,
        "spent": 4200.0
    },
    {
        "id": "5b8c3d2e-5678-1234-dcba-fedcba987654",
        "label": "Alimentación",
        "icon": "🍔",
        "color": "#34d399",
        "limit": 3000.0,
        "spent": 1850.0
    }
]
```

> `spent` se calcula en tiempo real — no se guarda en la BD.

---

### PUT /budgets/:id

Actualiza el límite mensual de un presupuesto.

**Auth:** Requerida

**URL ejemplo:** `PUT {{baseUrl}}/budgets/4a7b2c1d-1234-5678-abcd-ef0123456789`

**Body:**
```json
{ "limit": 6000 }
```

**Respuesta `200`:**
```json
{
    "id": "4a7b2c1d-1234-5678-abcd-ef0123456789",
    "label": "Vivienda",
    "icon": "🏠",
    "color": "#60a5fa",
    "limit": 6000.0,
    "spent": 4200.0
}
```

**Errores:**
| Status | Mensaje |
|---|---|
| `404` | `"Presupuesto no encontrado"` |

---

## 5. PERFIL

### GET /profile

**Auth:** Requerida

**Respuesta `200`:**
```json
{
    "id": 1,
    "name": "Juan Pérez",
    "email": "juan@correo.com",
    "avatarUrl": "https://res.cloudinary.com/.../foto.jpg",
    "timezone": "America/Mexico_City",
    "monthStartDay": 1,
    "notifications": {
        "budgetAlert": false,
        "dailyReminder": false
    }
}
```

---

### PUT /profile

Actualiza nombre y/o email.

**Auth:** Requerida

**Body:**
```json
{
    "name": "Juan Nuevo",
    "email": "nuevo@correo.com"
}
```

**Respuesta `200`:** Perfil completo actualizado.

**Errores:**
| Status | Mensaje |
|---|---|
| `400` | `"Email ya en uso"` |

---

### PUT /profile/password

**Auth:** Requerida

**Body:**
```json
{
    "currentPassword": "contraseñaActual",
    "newPassword": "contraseñaNueva"
}
```

**Respuesta `204`:** Sin cuerpo.

**Errores:**
| Status | Mensaje |
|---|---|
| `400` | `"Contraseña incorrecta"` |

---

### POST /profile/avatar

Sube foto de perfil a Cloudinary.

**Auth:** Requerida
**Content-Type:** `multipart/form-data`
**Campo:** `avatar` → archivo de imagen (jpg, png, etc.)

**Respuesta `200`:**
```json
{ "avatarUrl": "https://res.cloudinary.com/finanzly/image/upload/..." }
```

**Cómo probarlo en Postman:**
1. Body → `form-data`
2. Key: `avatar` → tipo **File** → seleccionar imagen

---

### PUT /profile/preferences

**Auth:** Requerida

**Body:**
```json
{
    "timezone": "America/Monterrey",
    "monthStartDay": 15
}
```

**Valores válidos `timezone`:** `America/Mexico_City` · `America/Monterrey` · `America/Tijuana` · `America/Cancun`

**Valores válidos `monthStartDay`:** `1` · `5` · `10` · `15` · `16`

**Respuesta `200`:** Perfil completo actualizado.

**Errores:**
| Status | Mensaje |
|---|---|
| `400` | `"Timezone inválido"` |
| `400` | `"monthStartDay inválido"` |

---

### PUT /profile/notifications

**Auth:** Requerida

**Body:**
```json
{
    "budgetAlert": true,
    "dailyReminder": false
}
```

**Respuesta `200`:** Perfil completo actualizado.

---

### DELETE /profile

Elimina la cuenta y todos sus datos (transacciones y presupuestos).

**Auth:** Requerida

**Respuesta `204`:** Sin cuerpo.

> ⚠️ Acción irreversible.

---

## Referencia: Categorías predefinidas

| Categoría | Icon | Color |
|---|---|---|
| Vivienda | 🏠 | `#60a5fa` |
| Alimentación | 🍔 | `#34d399` |
| Transporte | 🚗 | `#fbbf24` |
| Salud | 💊 | `#f87171` |
| Ocio | 🎬 | `#a78bfa` |
| Educación | 📚 | `#38bdf8` |
| Ropa | 👕 | `#fb7185` |
| Servicios | 💡 | `#a3e635` |
| Ahorro | 💰 | `#4ade80` |
| Otros | 📦 | `#94a3b8` |

---

## Lógica del mes activo

El período se calcula usando `monthStartDay` del perfil del usuario.

**Ejemplo con `monthStartDay = 15`:**

| Fecha de hoy | Inicio del mes activo | Fin |
|---|---|---|
| 20 de Abril | 15 de Abril | 14 de Mayo |
| 10 de Abril | 15 de Marzo | 14 de Abril |

**Ejemplo con `monthStartDay = 1` (default):**

| Fecha de hoy | Inicio | Fin |
|---|---|---|
| Cualquier día de Abril | 1 de Abril | 30 de Abril |

> Afecta a: `/transactions/summary`, `/transactions/categories` y el campo `spent` de `/budgets`.

---

## Flujo de prueba completo en Postman

Seguir este orden para probar todo desde cero:

```
1.  POST /auth/register              → token se guarda automático (ver Test script)
2.  GET  /auth/me                    → verificar onboardingCompleted: false
3.  POST /onboarding                 → configurar ingreso y categorías
4.  GET  /auth/me                    → verificar onboardingCompleted: true
5.  POST /transactions               → crear un ingreso (type: "ingreso")
6.  POST /transactions               → crear 2-3 gastos con distintas categorías
7.  GET  /transactions               → listar todas
8.  GET  /transactions/summary       → ver balance del mes activo
9.  GET  /transactions/categories    → ver distribución porcentual
10. GET  /budgets                    → ver límites y spent calculado
11. PUT  /budgets/:id                → cambiar límite de un presupuesto
12. GET  /profile                    → ver perfil completo
13. PUT  /profile/preferences        → cambiar monthStartDay a 15
14. GET  /transactions/summary       → verificar que el período cambió
15. PUT  /profile/notifications      → activar budgetAlert: true
16. PUT  /profile/password           → cambiar contraseña
17. POST /auth/login                 → login con la nueva contraseña
18. GET  /transactions/export?format=csv&token={{token}}  → descargar CSV
19. POST /transactions/import        → reimportar el CSV descargado
20. DELETE /profile                  → eliminar cuenta (prueba final)
```

---

## Rutas legacy (siguen funcionando para compatibilidad)

| Path nuevo (spec) | Path legacy |
|---|---|
| `POST /auth/register` | `POST /api/register/` |
| `POST /auth/login` | `POST /api/login/` |
| `POST /auth/logout` | `POST /api/logout/` |
| `POST /api/token/refresh/` | igual, no cambió |
