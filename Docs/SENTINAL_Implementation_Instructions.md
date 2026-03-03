# SENTINAL – Portable Offline AI System  
Implementation Instructions for Claude AI

You are now the lead developer tasked with implementing **SENTINAL**, a production-grade, offline-first, portable LLM deployment system.  

The system runs on **removable USB/SD media** (exFAT formatted), with a native **Android 15+ (SDK 35)** app and a **Linux** static runtime fallback. Core inference uses **llama.cpp** (GGUF models via mmap), domain knowledge in encrypted **SQLite + SQLCipher + FTS5** DB packs, atomic/power-loss-safe updates, persistent **SAF** access on Android, and strict hardening.

**Authoritative Source**: Everything below is derived from the project's Technical Design & Production Manual (TDM) located at:  
https://github.com/jerimie81/SENTINAL/blob/main/Docs/Flash-AI_Technical-Design-Manual-(TDM)

**Current Repo State** (as of March 2026):  
- GitHub: https://github.com/jerimie81/SENTINAL  
- No source code committed yet — only README.md and /Docs/ folder with the TDM text file.  
- Very early stage: design complete, implementation pending.  
- License: None yet (use MIT when creating files).

## Hard Rules – Do NOT Violate

1. **Three Gates must be satisfied before considering any part "production-ready"**:
   - G1: SAF Durability (persistent USB/SD access across reboots, no re-prompts)
   - G2: Offline Inference Stability (llama.cpp mmap, 10-min sustained generation, no OOM/thermal crash)
   - G3: Atomic DB Pack Update (survives power loss / USB yank mid-swap)

2. Android target: **SDK 35**, **arm64-v8a**, **NDK r26+**, **CMake 3.22+**, **-O2 -fopenmp**, **16KB page alignment**.

3. **NEVER** use file paths for models/DBs on Android — always use ParcelFileDescriptor + fd passing to JNI.

4. **Encryption**:
   - Models (AI/models/): plaintext (for mmap performance)
   - DB packs & user data: SQLCipher (full DB encryption)
   - Loose files in UserSpace/: XChaCha20 + Argon2id

5. **Media layout is fixed** (exFAT only):



####

AI/
models/             ← GGUF files, read-only, no encryption
runtime/linux/      ← static llama-cli binary
config/
Databases/
domain_packs/       ← encrypted .sqlite packs + .sha256
user_data/          ← user-specific encrypted DBs
UserSpace/
projects/
logs/
temp/               ← staging for atomic updates
text6. Code style:
- Clean, modular, RAII where possible (C++/JNI)
- Extensive logging (android.util.Log + file logs in UserSpace/logs/)
- Error handling: every critical call checked, user-friendly messages
- Thread safety: connection pools, mutexes for shared state

## Priority Implementation Order (Follow Sequentially)

### Phase 1 – Foundation & Gates (Critical – Complete First)

1. **Android SAF Permission Persistence Module** (Java/Kotlin)  
Goal: Achieve G1.  
- Create a utility class `PersistentStorageAccess`  
- Methods: requestTreeUri(), persistUri(Uri), rehydrateUri(), listFilesInTree(), etc.  
- Store encrypted URI in EncryptedSharedPreferences (MasterKey + AES256).  
- Handle permission recovery on cold start / force-stop.  
- Include torture-test helper: write/read/rename/delete across reboots.

2. **llama.cpp Android NDK Build & JNI Wrapper** (C++/CMake + Java)  
Goal: Achieve G2 basics.  
- Set up `android-app/cpp/CMakeLists.txt` for llama.cpp subset  
  - Include only needed sources (no server, no examples beyond basics)  
  - Flags: -DUSE_OPENMP=1 -DCMAKE_BUILD_TYPE=Release -DANDROID_PLATFORM=android-35  
- JNI interface (at minimum):
  ```cpp
  JNIEXPORT jint JNICALL Java_com_sentinal_inference_LlamaNative_loadModel(
      JNIEnv*, jobject, jint fd, jint contextSize, jint gpuLayers);
  JNIEXPORT jstring JNICALL Java_com_sentinal_inference_LlamaNative_generateTokens(...);

Load via mmap from ParcelFileDescriptor fd (NOT path string).
Simple test activity: load 3B Q4 GGUF → generate 128 tokens → log tok/s & RSS.


Atomic DB Pack Update Logic (Java + SQLite/SQLCipher via JNI)
Goal: Achieve G3.
Class: DomainPackManager
Flow: download/stage in temp/ → verify SHA-256 → fsync → atomic rename → reopen DB pool
Use WAL mode + PRAGMA synchronous=NORMAL
Handle interruptions (power loss simulation via USB eject).


Phase 2 – Core App Structure

Main Android App Scaffold (Kotlin preferred)
MainActivity: SAF picker on first launch, persist URI, show status dashboard
Fragments/Screens: Model Loader, Inference Chat, Benchmark, Settings
Service for background inference if needed (but prefer foreground initially)

DB Pack Integration
NDK-build SQLCipher + SQLite with FTS5
JNI helpers: openEncryptedDb(int fd, String key), queryFts(String term), etc.
Connection pooling (limit 4–8 connections)


Phase 3 – Polish & Production

Benchmark harness
Linux static runtime (llama-cli with same DB logic via plain SQLite/SQLCipher)
DB pack builder scripts (Python on secure host: schema → populate → encrypt → sign)
CI pipeline skeleton (.github/workflows/)
SAF torture test app/service

Immediate Next Steps for You (Claude)
Start with Phase 1 — produce code in this order:

PersistentStorageAccess.kt – full SAF persistence implementation with recovery
CMakeLists.txt + basic JNI loader in cpp/ for llama.cpp
Simple LlamaNative.java / .kt wrapper + test in MainActivity

For each file:

Provide full file path (e.g. android-app/app/src/main/java/com/sentinal/storage/PersistentStorageAccess.kt)
Include imports, comments, error handling
Suggest next logical file after the current one

Ask clarifying questions only if something in the TDM is ambiguous — otherwise proceed aggressively toward passing the three gates.
Begin coding now. Output the first file(s) with complete code.

