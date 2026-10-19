## customers

One row per customer.

| column | type | notes |
|---|---|---|
| customer_id | integer | primary key |
| first_name | text | |
| last_name | text | |
| email | text | |
| mobile_number | text | includes dial code |
| marketing_opt_in_flag | text | mixed values, see below |
| email_verified_flag | text | mixed values, see below |
| sex | text | |
| created_at | timestamp | |
| updated_at | timestamp | |

**Messy on purpose:**
- Inconsistent casing and stray leading/trailing whitespace in text columns (names, email, sex).
- Flags mix `true`/`false`, `yes`/`no` and `1`/`0`.