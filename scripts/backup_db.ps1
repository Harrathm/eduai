<#
.SYNOPSIS
    Backup de la base de données PostgreSQL EDUAI Learning.

.DESCRIPTION
    Crée un backup compressé (.sql.gz) de la base de données.
    Conserve les N derniers backups selon la politique de rétention.

.PARAMETER DatabaseUrl
    URL de connexion PostgreSQL (défaut: lit depuis .env).

.PARAMETER RetentionDays
    Nombre de jours de rétention des backups (défaut: 30).

.EXAMPLE
    .\backup_db.ps1
    .\backup_db.ps1 -RetentionDays 7
#>
param(
    [string]$DatabaseUrl = "",
    [int]$RetentionDays = 30
)

$ErrorActionPreference = "Stop"

# --- Configuration ---
$BackupDir = Join-Path $PSScriptRoot "..\backups"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "eduai_backup_$Timestamp.sql"
$BackupGz = "$BackupFile.gz"
$BackupPath = Join-Path $BackupDir $BackupGz

# --- Parse DATABASE_URL ---
if (-not $DatabaseUrl) {
    $EnvFile = Join-Path $PSScriptRoot "..\backend\.env"
    if (Test-Path $EnvFile) {
        $lines = Get-Content $EnvFile | Where-Object { $_ -match "^DATABASE_URL=" }
        if ($lines) {
            $DatabaseUrl = ($lines -split "=", 2)[1].Trim()
        }
    }
}

if (-not $DatabaseUrl) {
    Write-Error "DATABASE_URL non définie. Passez -DatabaseUrl ou créez backend\.env"
    exit 1
}

# Extraire les composants de l'URL
# Format: postgresql+pg8000://user:pass@host:port/dbname
$Pattern = 'postgresql\+\w+://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
if ($DatabaseUrl -match $Pattern) {
    $DbUser = $Matches[1]
    $DbPass = $Matches[2]
    $DbHost = $Matches[3]
    $DbPort = $Matches[4]
    $DbName = $Matches[5]
} else {
    Write-Error "Format DATABASE_URL non reconnu: $DatabaseUrl"
    exit 1
}

# --- Créer le dossier de backup ---
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Write-Host "[OK] Dossier de backup créé: $BackupDir" -ForegroundColor Green
}

# --- Exécuter pg_dump ---
Write-Host "[...] Backup de la base $DbName sur $DbHost`:$DbPort ..." -ForegroundColor Cyan

$env:PGPASSWORD = $DbPass
$TempFile = Join-Path $BackupDir $BackupFile

try {
    & pg_dump -h $DbHost -p $DbPort -U $DbUser -d $DbName --no-owner --no-privileges -F p -f $TempFile 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump a échoué avec le code $LASTEXITCODE"
    }

    # Compresser avec gzip
    $source = $TempFile
    $dest = $BackupPath
    $in = [System.IO.File]::OpenRead($source)
    $out = [System.IO.File]::Create($dest)
    $gz = [System.IO.Compression.GZipStream]::new($out, [System.IO.Compression.CompressionLevel]::Optimal)
    $in.CopyTo($gz)
    $gz.Close()
    $in.Close()
    $out.Close()
    Remove-Item $TempFile

    $sizeMB = [math]::Round((Get-Item $dest).Length / 1MB, 2)
    Write-Host "[OK] Backup créé: $BackupPath ($sizeMB MB)" -ForegroundColor Green
} catch {
    Write-Error "Erreur lors du backup: $_"
    if (Test-Path $TempFile) { Remove-Item $TempFile }
    exit 1
} finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}

# --- Rétention : supprimer les vieux backups ---
Write-Host "[...] Nettoyage des backups de plus de $RetentionDays jours ..." -ForegroundColor Cyan
$cutoff = (Get-Date).AddDays(-$RetentionDays)
$oldBackups = Get-ChildItem -Path $BackupDir -Filter "eduai_backup_*.sql.gz" |
    Where-Object { $_.LastWriteTime -lt $cutoff }

if ($oldBackups) {
    foreach ($old in $oldBackups) {
        Remove-Item $old.FullName
        Write-Host "  Supprimé: $($old.Name)" -ForegroundColor Yellow
    }
    Write-Host "[OK] $($oldBackups.Count) backup(s) supprimé(s)" -ForegroundColor Green
} else {
    Write-Host "[OK] Aucun backup à supprimer" -ForegroundColor Green
}

# --- Résumé ---
$totalBackups = (Get-ChildItem -Path $BackupDir -Filter "eduai_backup_*.sql.gz").Count
$totalSizeMB = [math]::Round(((Get-ChildItem -Path $BackupDir -Filter "eduai_backup_*.sql.gz" | Measure-Object -Property Length -Sum).Sum / 1MB), 2)
Write-Host ""
Write-Host "=== Résumé ===" -ForegroundColor Cyan
Write-Host "  Backups conservés: $totalBackups"
Write-Host "  Taille totale:    $totalSizeMB MB"
Write-Host "  Dernier backup:   $BackupGz"
