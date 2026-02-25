Perform a thorough security analysis of this codebase. Cover all major vulnerability classes, surface concrete findings with file locations and line numbers, and propose specific fixes for each issue found. Do not produce vague warnings - find actual problems or explain clearly why each class of issue is not present.

## Context Bootstrap

Before starting, check whether `/deep-learn` has already been run on this codebase:

```bash
cat .claude-learning-metadata.json 2>/dev/null
cat .claude-learning/manifest.json 2>/dev/null
cat .claude-learning/security-mapper.json 2>/dev/null
cat .claude-learning/dependency-mapper.json 2>/dev/null
```

**If manifest.json exists**: Use `scope_boundaries.source` and `scope_boundaries.config` from the manifest to scope all grep commands below — target those directories instead of searching `.` blindly. Skip `scope_boundaries.vendor` and `scope_boundaries.generated`.

**If security-mapper.json exists**: Load the prior findings. In your analysis, focus on extending them — verify the listed findings are still present, check if they've been partially addressed, and look for new issues introduced since the last run. Note which prior findings appear resolved.

**If dependency-mapper.json exists**: Use `api_surface` to get the full list of routes for Phase 4 (auth coverage). Use `external_services` to understand what external systems handle sensitive data.

**If no context exists**: Proceed with the phases below, doing full discovery.

## Phase 1: Reconnaissance

Identify the attack surface:
1. What does this application do? What are its trust boundaries?
2. What data does it handle? (PII, financial, credentials, health data?)
3. What are the entry points? (HTTP endpoints, CLI args, file inputs, message queues?)
4. What are the exit points? (databases, external APIs, file system, network)
5. What authentication/authorization mechanisms are in place?

## Phase 2: Secrets and Credential Exposure

Search for hardcoded secrets, tokens, passwords, and keys:

```bash
# Common secret patterns
grep -rn --include="*.js" --include="*.ts" --include="*.py" --include="*.go" --include="*.rb" --include="*.java" --include="*.env" --include="*.yaml" --include="*.yml" --include="*.json" \
  -E "(password|passwd|secret|api_key|apikey|api-key|token|auth_token|access_key|private_key|client_secret)\s*[=:]\s*['\"][^'\"]{8,}" . \
  | grep -v "test\|spec\|mock\|example\|placeholder\|your_\|<\|TODO\|FIXME" \
  | grep -v "node_modules\|vendor\|.git"

# Check .env files that might be committed
find . -name ".env*" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null

# Check for AWS/GCP/Azure credential patterns
grep -rn "AKIA[0-9A-Z]{16}\|AIza[0-9A-Za-z-_]{35}\|ya29\." . --include="*.js" --include="*.ts" --include="*.py" --include="*.go" 2>/dev/null | grep -v ".git"
```

Read any `.gitignore` to see what's explicitly excluded - note if `.env` is missing from it.

## Phase 3: Injection Vulnerabilities

### SQL Injection
Search for string concatenation in database queries:

```bash
grep -rn --include="*.js" --include="*.ts" --include="*.py" --include="*.go" --include="*.rb" --include="*.java" \
  -E "(query|execute|exec|db\.)\s*\(.*\+|f\"|f'|format\(|%s|%d.*sql|SELECT|INSERT|UPDATE|DELETE" . \
  | grep -v "node_modules\|vendor\|test\|spec" | head -30
```

### Command Injection
Search for shell execution with user-controlled input:

```bash
grep -rn --include="*.js" --include="*.ts" --include="*.py" --include="*.go" --include="*.rb" \
  -E "(exec|spawn|system|popen|subprocess|child_process|os\.system|eval|Function\()" . \
  | grep -v "node_modules\|vendor\|test\|spec" | head -30
```

### Path Traversal
Search for file operations with user input:

```bash
grep -rn --include="*.js" --include="*.ts" --include="*.py" --include="*.go" \
  -E "(readFile|open|path\.join|filepath\.|os\.Open|ioutil\.ReadFile)" . \
  | grep -v "node_modules\|vendor\|test\|spec" | head -30
```

## Phase 4: Authentication and Authorization

1. Find all authentication middleware/decorators - are they applied consistently?
2. Find all authorization checks - look for endpoints that might be missing them
3. Check session management: token storage, expiry, invalidation on logout
4. Check password handling: hashing algorithm (bcrypt/argon2 good; MD5/SHA1/plain bad)
5. Check for insecure direct object references (IDOR) - can user A access user B's data by changing an ID?

```bash
# Find auth-related code
grep -rn --include="*.js" --include="*.ts" --include="*.py" --include="*.go" \
  -E "(authenticate|authorize|middleware|guard|permission|role|jwt|session|cookie)" . \
  | grep -v "node_modules\|vendor\|test" | head -40
```

## Phase 5: Cryptography

1. Identify all uses of cryptographic functions
2. Flag weak algorithms: MD5, SHA1, DES, RC4, ECB mode AES
3. Check for hardcoded salts or IVs
4. Check for improper random number generation (Math.random() for security purposes)

```bash
grep -rn --include="*.js" --include="*.ts" --include="*.py" --include="*.go" \
  -E "(md5|sha1|des|rc4|Math\.random|rand\.Rand|crypto\.|hashlib\.|bcrypt)" . \
  | grep -v "node_modules\|vendor\|test\|spec" | head -30
```

## Phase 6: XSS and Input Handling (Web Applications)

1. Find all places user input is rendered into HTML
2. Check for missing output encoding
3. Check Content Security Policy headers
4. Find any use of `innerHTML`, `dangerouslySetInnerHTML`, `document.write`, `eval`

```bash
grep -rn --include="*.js" --include="*.ts" --include="*.html" \
  -E "(innerHTML|dangerouslySetInnerHTML|document\.write|\.html\(|eval\(|v-html)" . \
  | grep -v "node_modules\|vendor\|test" | head -20
```

## Phase 7: Dependency Vulnerabilities

Note: Run `/dep-audit` for full dependency analysis. Here, flag any obviously dangerous patterns:

```bash
# Check for known vulnerable package versions if lockfiles exist
cat package-lock.json 2>/dev/null | grep -E '"(version|resolved)"' | head -50
```

## Phase 8: Security Headers and Configuration

For web applications, check for:
1. CORS configuration - is it overly permissive (`*`)?
2. Security headers (HSTS, X-Frame-Options, X-Content-Type-Options, CSP)
3. Rate limiting on sensitive endpoints
4. Error messages that leak stack traces or internal details

```bash
grep -rn --include="*.js" --include="*.ts" --include="*.py" --include="*.go" \
  -E "(cors|CORS|Access-Control|helmet|security.*header|rate.?limit)" . \
  | grep -v "node_modules\|vendor\|test" | head -20
```

## Phase 9: Synthesis

Produce a structured security report:

**Attack Surface Summary**: What this application exposes and to whom.

**Findings** (for each finding):
- **Severity**: Critical / High / Medium / Low / Informational
- **Category**: (Injection / Auth / Crypto / XSS / Secrets / etc.)
- **Location**: `file:line_number`
- **Description**: What the vulnerability is and how it could be exploited
- **Proposed Fix**: Specific code change to remediate it

**What Looks Good**: Security controls that are implemented correctly.

**What Couldn't Be Determined**: Issues that require runtime analysis or penetration testing to fully assess.

**Prioritized Remediation Plan**: Fix Critical findings immediately, then High, then Medium.

$ARGUMENTS
