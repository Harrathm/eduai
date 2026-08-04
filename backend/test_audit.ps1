$ErrorActionPreference = "Stop"
$BASE = "http://localhost:8000"

function Login($email, $pass) {
    $r = Invoke-RestMethod -Uri "$BASE/auth/login" -Method POST -Body "username=$email&password=$pass" -ContentType "application/x-www-form-urlencoded" -ErrorAction SilentlyContinue
    if ($r.access_token) { return $r.access_token }
    Write-Host "  [FAIL] LOGIN $email"
    return $null
}

function GET($path, $token) {
    $h = @{ "Authorization" = "Bearer $token" }
    try {
        $r = Invoke-WebRequest -Uri "$BASE$path" -Method GET -Headers $h -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        return @{ code = $r.StatusCode; body = ($r.Content | ConvertFrom-Json) }
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        return @{ code = $code; body = $null }
    }
}

function POST($path, $token, $data) {
    $h = @{ "Authorization" = "Bearer $token"; "Content-Type" = "application/json" }
    try {
        $body = $data | ConvertTo-Json -Depth 10
        $r = Invoke-WebRequest -Uri "$BASE$path" -Method POST -Headers $h -Body $body -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        return @{ code = $r.StatusCode; body = ($r.Content | ConvertFrom-Json) }
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        try {
            $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
            $errBody = $reader.ReadToEnd()
            return @{ code = $code; body = ($errBody | ConvertFrom-Json) }
        } catch {
            return @{ code = $code; body = $null }
        }
    }
}

function DELETE($path, $token) {
    $h = @{ "Authorization" = "Bearer $token" }
    try {
        $r = Invoke-WebRequest -Uri "$BASE$path" -Method DELETE -Headers $h -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        return @{ code = $r.StatusCode; body = ($r.Content | ConvertFrom-Json) }
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        return @{ code = $code; body = $null }
    }
}

$pass = "passeword123"
$ok = 0; $fail = 0

function Check($label, $cond, $actual, $expected) {
    if ($cond) { Write-Host "  [OK] $label"; $script:ok++ }
    else { Write-Host "  [FAIL] $label (got=$actual expected=$expected)"; $script:fail++ }
}

# === LOGIN ===
Write-Host "`n=== LOGIN ==="
$S1 = Login "eleve1.carthage@eduai.tn" $pass
$S2 = Login "eleve2.carthage@eduai.tn" $pass
$S3 = Login "eleve3.carthage@eduai.tn" $pass
$P  = Login "parent.carthage@eduai.tn" $pass
$P2 = Login "parent.eljem@eduai.tn" $pass
Check "Student1 login" ($null -ne $S1)
Check "Student2 login" ($null -ne $S2)
Check "Student3 login" ($null -ne $S3)
Check "Parent login" ($null -ne $P)
Check "Parent2 login" ($null -ne $P2)

# === USER IDS ===
Write-Host "`n=== USER IDS ==="
$r = GET "/api/users/me" $S1
$u1 = $r.body; Write-Host "  S1: id=$($u1.id) school=$($u1.school_id) niveau=$($u1.niveau_scolaire)"
$r = GET "/api/users/me" $S2
$u2 = $r.body; Write-Host "  S2: id=$($u2.id) school=$($u2.school_id) niveau=$($u2.niveau_scolaire)"
$r = GET "/api/users/me" $S3
$u3 = $r.body; Write-Host "  S3: id=$($u3.id) school=$($u3.school_id) niveau=$($u3.niveau_scolaire)"
$r = GET "/api/users/me" $P
$pu = $r.body; Write-Host "  P:  id=$($pu.id) school=$($pu.school_id)"
$r = GET "/api/users/me" $P2
$pu2 = $r.body; Write-Host "  P2: id=$($pu2.id) school=$($pu2.school_id)"

# === PARENT: CHILDREN ===
Write-Host "`n=== PARENT: CHILDREN ==="
$r = GET "/api/parents/me/enfants" $P
Check "P GET enfants" ($r.code -eq 200) $r.code 200
Write-Host "  Data: $($r.body | ConvertTo-Json -Compress -Depth 5)"
$childIds = @()
if ($r.body.enfants) { $r.body.enfants | ForEach-Object { $childIds += $_.eleve_id } }
Write-Host "  Child IDs: $($childIds -join ', ')"

$r = GET "/api/parents/me/enfants" $P2
Check "P2 GET enfants" ($r.code -eq 200) $r.code 200
Write-Host "  Data: $($r.body | ConvertTo-Json -Compress -Depth 5)"

# === PARENT: DASHBOARD ===
Write-Host "`n=== PARENT: DASHBOARD ==="
$r = GET "/api/parents/me/dashboard" $P
Check "P GET dashboard" ($r.code -eq 200) $r.code 200
Write-Host "  Data: $($r.body | ConvertTo-Json -Compress -Depth 5)"

$r = GET "/api/parents/me/dashboard" $P2
Check "P2 GET dashboard" ($r.code -eq 200) $r.code 200

# === PARENT: CHILD SUIVI + PROGRESSION ===
Write-Host "`n=== PARENT: CHILD DETAIL ==="
if ($childIds.Count -gt 0) {
    $cid = $childIds[0]
    $r = GET "/api/parents/me/enfants/$cid/suivi" $P
    Check "P GET child suivi" ($r.code -eq 200) $r.code 200
    Write-Host "  Suivi: $($r.body | ConvertTo-Json -Compress -Depth 5)" | ForEach-Object { Write-Host $_.Substring(0, [Math]::Min(400, $_.Length)) }
    
    $r = GET "/api/parents/me/enfants/$cid/progression" $P
    Check "P GET child progression" ($r.code -eq 200) $r.code 200
    Write-Host "  Progression: $($r.body | ConvertTo-Json -Compress -Depth 5)" | ForEach-Object { Write-Host $_.Substring(0, [Math]::Min(400, $_.Length)) }
    
    # Isolation: fake child
    $r = GET "/api/parents/me/enfants/999999/suivi" $P
    Check "P GET fake child suivi (expect 404)" ($r.code -eq 404) $r.code 404
    
    # Cross-school: P2 trying P's child
    $r = GET "/api/parents/me/enfants/$cid/suivi" $P2
    Check "P2 (Eljem) GET Carthage child (expect 403/404)" ($r.code -eq 403 -or $r.code -eq 404) $r.code "403/404"
} else {
    Write-Host "  [SKIP] No children found"
}

# === PARENT: MESSAGES ===
Write-Host "`n=== PARENT: MESSAGES ==="
$r = GET "/api/parents/me/messages" $P
Check "P GET messages" ($r.code -eq 200) $r.code 200

# === PARENT: LINK/UNLINK ===
Write-Host "`n=== PARENT: LINK/UNLINK ==="
$r = POST "/api/parents/me/enfants/lier" $P @{ "email_eleve" = "nonexistent@xyz.com" }
Check "P link nonexistent (expect 404)" ($r.code -eq 404) $r.code 404

$r = DELETE "/api/parents/me/enfants/999999/delier" $P
Check "P unlink fake (expect 404)" ($r.code -eq 404) $r.code 404

# === PARENT: CREDIT WALLET ===
Write-Host "`n=== PARENT: CREDIT WALLET ==="
if ($childIds.Count -gt 0) {
    $cid = $childIds[0]
    $r = POST "/api/parents/me/enfants/$cid/credit-wallet" $P @{ "amount" = -1 }
    Check "P credit negative (expect 400/422)" ($r.code -eq 400 -or $r.code -eq 422) $r.code "400/422"
}

# === PARENT: FAMILLE ===
Write-Host "`n=== PARENT: FAMILLE ==="
$r = GET "/api/famille/compte" $P
Check "P GET famille/compte" ($r.code -eq 200 -or $r.code -eq 404) $r.code "200/404"
Write-Host "  $($r.code): $($r.body | ConvertTo-Json -Compress -Depth 3)"
$r = GET "/api/famille/enfants" $P
Check "P GET famille/enfants" ($r.code -eq 200 -or $r.code -eq 404) $r.code "200/404"

# ========================================
# STUDENT MODULE A: PÉDAGOGIQUE
# ========================================
Write-Host "`n=== MODULE A: PARCOURS ADAPTATIF ==="
$r = GET "/api/pathway/mon-parcours" $S1
Check "S1 mon-parcours" ($r.code -eq 200) $r.code 200

$r = GET "/api/pathway/catalog" $S1
Check "S1 pathway catalog" ($r.code -eq 200) $r.code 200

$r = GET "/api/pathway/matieres" $S1
Check "S1 matieres" ($r.code -eq 200) $r.code 200

$r = GET "/api/pathway/chapter-pathways" $S1
Check "S1 chapter-pathways" ($r.code -eq 200) $r.code 200

$r = GET "/api/pathway/notions-list" $S1
Check "S1 notions-list" ($r.code -eq 200) $r.code 200

# Assimilation profile
$r = GET "/api/pathway/eleves/$($u1.id)/profil-assimilation" $S1
Check "S1 own profil-assimilation" ($r.code -eq 200) $r.code 200

$r = GET "/api/pathway/eleves/$($u2.id)/profil-assimilation" $S1
Check "S1 -> S2 profil-assimilation (expect 403)" ($r.code -eq 403) $r.code 403

# Effective access
$r = GET "/api/pathway/eleves/$($u1.id)/acces-effectif" $S1
Check "S1 own acces-effectif" ($r.code -eq 200) $r.code 200

$r = GET "/api/pathway/eleves/$($u2.id)/acces-effectif" $S1
Check "S1 -> S2 acces-effectif (expect 403)" ($r.code -eq 403) $r.code 403

# Score submission
$r = POST "/api/pathway/scores" $S1 @{ "eleve_id" = $u1.id; "chapitre_id" = 1; "notion_id" = 1; "score" = 55.0; "source" = "quiz" }
Check "S1 score own (expect 200/201/404)" ($r.code -in @(200,201,404)) $r.code "200/201/404"

$r = POST "/api/pathway/scores" $S1 @{ "eleve_id" = $u2.id; "chapitre_id" = 1; "notion_id" = 1; "score" = 99.0; "source" = "quiz" }
Check "S1 score S2 (expect 403)" ($r.code -eq 403) $r.code 403

# ========================================
# STUDENT MODULE B: COMMERCIAL
# ========================================
Write-Host "`n=== MODULE B: WALLET ==="
$r = GET "/api/wallet/balance" $S1
Check "S1 wallet balance" ($r.code -eq 200) $r.code 200
Write-Host "  Balance: $($r.body | ConvertTo-Json -Compress -Depth 5)"

$r = GET "/api/wallet/history?page=1&page_size=5" $S1
Check "S1 wallet history" ($r.code -eq 200) $r.code 200

Write-Host "`n=== MODULE B: PACKS ==="
$r = GET "/api/packs" $S1
Check "S1 GET packs" ($r.code -eq 200) $r.code 200

$r = GET "/api/abonnements/packs" $S1
Check "S1 GET abonnements/packs" ($r.code -eq 200) $r.code 200

$r = GET "/api/abonnements/mes-abonnements" $S1
Check "S1 GET mes-abonnements" ($r.code -eq 200) $r.code 200
Write-Host "  Abonnements: $($r.body | ConvertTo-Json -Compress -Depth 5)"

Write-Host "`n=== MODULE B: COURSE ACCESS ==="
$r = GET "/api/learner/my-courses" $S1
Check "S1 GET learner/my-courses" ($r.code -eq 200) $r.code 200

$r = GET "/api/academy/courses" $S1
Check "S1 GET academy/courses" ($r.code -eq 200) $r.code 200

# ========================================
# LEARNER DASHBOARD & GOALS
# ========================================
Write-Host "`n=== LEARNER DASHBOARD & GOALS ==="
$r = GET "/api/learner/dashboard" $S1
Check "S1 GET learner/dashboard" ($r.code -eq 200) $r.code 200

$r = GET "/api/learner/daily-objective" $S1
Check "S1 GET daily-objective" ($r.code -eq 200) $r.code 200

$r = GET "/api/learner/recommended-path" $S1
Check "S1 GET recommended-path" ($r.code -eq 200) $r.code 200

$r = GET "/api/learner/goals" $S1
Check "S1 GET goals" ($r.code -eq 200) $r.code 200

$r = GET "/api/learner/goals/summary" $S1
Check "S1 GET goals/summary" ($r.code -eq 200) $r.code 200

$r = GET "/api/learner/goals/report" $S1
Check "S1 GET goals/report" ($r.code -eq 200) $r.code 200

# ========================================
# GAMIFICATION
# ========================================
Write-Host "`n=== GAMIFICATION ==="
$r = GET "/api/gamification/badges" $S1
Check "S1 GET badges" ($r.code -eq 200) $r.code 200

$r = GET "/api/gamification/streak" $S1
Check "S1 GET streak" ($r.code -eq 200) $r.code 200

$r = GET "/api/gamification/rankings" $S1
Check "S1 GET rankings" ($r.code -eq 200) $r.code 200

# ========================================
# AI
# ========================================
Write-Host "`n=== AI ==="
$r = GET "/api/ai/history" $S1
Check "S1 GET ai/history" ($r.code -eq 200) $r.code 200

$r = GET "/api/ai/usage" $S1
Check "S1 GET ai/usage" ($r.code -eq 200) $r.code 200

$r = GET "/api/ai/stats" $S1
Check "S1 GET ai/stats" ($r.code -eq 200) $r.code 200

# ========================================
# CONVERSATIONS
# ========================================
Write-Host "`n=== CONVERSATIONS ==="
$r = GET "/api/conversations" $S1
Check "S1 GET conversations" ($r.code -eq 200) $r.code 200

# ========================================
# CERTIFICATES
# ========================================
Write-Host "`n=== CERTIFICATES ==="
$r = GET "/api/learner/certificates" $S1
Check "S1 GET certificates" ($r.code -eq 200) $r.code 200

# ========================================
# PLACEMENT
# ========================================
Write-Host "`n=== PLACEMENT ==="
$r = GET "/api/placement/tests" $S1
Check "S1 GET placement/tests" ($r.code -eq 200) $r.code 200

# ========================================
# INBOX
# ========================================
Write-Host "`n=== INBOX ==="
$r = GET "/api/inbox/messages?skip=0&limit=5" $S1
Check "S1 GET inbox" ($r.code -eq 200) $r.code 200

# ========================================
# LMS
# ========================================
Write-Host "`n=== LMS ==="
$r = GET "/api/lms/my-classes" $S1
Check "S1 GET lms/my-classes" ($r.code -eq 200 -or $r.code -eq 404) $r.code "200/404"

$r = GET "/api/lms/assignments" $S1
Check "S1 GET lms/assignments" ($r.code -eq 200 -or $r.code -eq 404) $r.code "200/404"

$r = GET "/api/lms/progress" $S1
Check "S1 GET lms/progress" ($r.code -eq 200 -or $r.code -eq 404) $r.code "200/404"

# ========================================
# BIBLIOTHEQUE
# ========================================
Write-Host "`n=== BIBLIOTHEQUE ==="
$r = GET "/api/bibliotheque/search?q=math" $S1
Check "S1 GET bibliotheque/search" ($r.code -eq 200) $r.code 200

$r = GET "/api/bibliotheque/competences" $S1
Check "S1 GET bibliotheque/competences" ($r.code -eq 200) $r.code 200

# ========================================
# ELEMENTS
# ========================================
Write-Host "`n=== ELEMENTS ==="
$r = GET "/api/elements" $S1
Check "S1 GET elements" ($r.code -eq 200) $r.code 200

# ========================================
# SUBSCRIPTIONS
# ========================================
Write-Host "`n=== SUBSCRIPTIONS ==="
$r = GET "/api/subscriptions/plans" $S1
Check "S1 GET subscriptions/plans" ($r.code -eq 200) $r.code 200

$r = GET "/api/subscriptions/current" $S1
Check "S1 GET subscriptions/current" ($r.code -eq 200) $r.code 200

# ========================================
# CROSS-ROLE ISOLATION
# ========================================
Write-Host "`n=== CROSS-ROLE ISOLATION ==="
$r = GET "/api/parents/me/dashboard" $S1
Check "S1 -> P dashboard (expect 403)" ($r.code -eq 403) $r.code 403

$r = GET "/api/parents/me/enfants" $S1
Check "S1 -> P enfants (expect 403)" ($r.code -eq 403) $r.code 403

$r = GET "/api/learner/goals" $P
Check "P -> S goals (check access)" ($r.code -in @(200,403)) $r.code "200/403"

$r = GET "/api/pathway/mon-parcours" $P
Check "P -> S mon-parcours (check access)" ($r.code -in @(200,403)) $r.code "200/403"

$r = GET "/api/gamification/badges" $P
Check "P -> S badges (check access)" ($r.code -in @(200,403)) $r.code "200/403"

# ========================================
# SUMMARY
# ========================================
Write-Host "`n========================================"
Write-Host "RESULTS: $ok passed, $fail failed"
Write-Host "========================================"
