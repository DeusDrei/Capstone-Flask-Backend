# Database Migration Instructions

## Changes Made

### 1. Added `semester` field to `instructionalmaterials` table
- Type: VARCHAR(20)
- Nullable: Yes
- Example values: "1st semester", "2nd semester"

### 2. Added `rank` field to `users` table
- Type: VARCHAR(100)
- Nullable: Yes
- Example values: "Professor", "Associate Professor", "Assistant Professor", "Instructor"

## Migration Commands

Run these commands in order:

```bash
# Generate migration
flask db migrate -m "Add semester to instructionalmaterials and rank to users"

# Review the generated migration file in migrations/versions/

# Apply migration
flask db upgrade
```

## Manual SQL (if needed)

If Flask-Migrate doesn't work, run these SQL commands directly:

```sql
-- Add semester column to instructionalmaterials
ALTER TABLE instructionalmaterials ADD COLUMN semester VARCHAR(20) NULL;

-- Add rank column to users
ALTER TABLE users ADD COLUMN rank VARCHAR(100) NULL;
```

## Verify Migration

```sql
-- Check instructionalmaterials table
DESCRIBE instructionalmaterials;

-- Check users table
DESCRIBE users;
```

## Update Existing Data (Optional)

```sql
-- Set default semester for existing IMs
UPDATE instructionalmaterials SET semester = '1st semester' WHERE semester IS NULL;

-- Set default rank for existing faculty
UPDATE users SET rank = 'Instructor' WHERE role = 'Faculty' AND rank IS NULL;
```
