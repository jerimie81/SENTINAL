# SENTINAL – Flash-based AI

Experimental project exploring **AI inference** directly inside Adobe Flash runtimes (ActionScript 3 / SWF), targeting legacy hardware, retro computing, air-gapped environments, or modern in-browser playback via emulators like Ruffle.

**Core concept**: Lightweight neural network execution using the Flash sandbox — combining 2000s-era runtime constraints with modern ML ideas.

## Project Status

- **Very early / conceptual phase**  
- No source code committed yet  
- Repository currently contains only basic setup files  
- Original technical design manual (TDM PDF) was present but appears removed or relocated — if you have an updated version, re-upload it (ideally to `/docs/`) and link below

## Goals & Motivation

- Demonstrate ML feasibility in extremely constrained environments (~few MB runtime)  
- Leverage Flash's vector math, BitmapData, and timers for inference loops  
- Run simple models (e.g. small MLPs, basic conv nets) on old PCs, via AIR, or Ruffle in browsers  
- Explore sandboxed / isolated AI execution (Flash VM security model)  
- Retro-computing + AI crossover appeal

## Planned Components

- ActionScript 3 tensor/math library (matmul, activations, etc.)  
- Minimal inference engine loop using enterFrame / Timer  
- Custom model format serialized into SWF-friendly binary  
- Python-based converter from ONNX / PyTorch → Flash model  
- Demos: XOR solver, MNIST subset, or tiny game AI  
- Performance tests under Ruffle vs. native Flash Player (where possible)

## Getting Started (once code arrives)

1. Install Ruffle browser extension or use https://ruffle.rs demo page  
2. Compile ActionScript with Flex SDK / OpenFL / manual tools  
3. Load SWF containing the model + inference code  
4. Watch AI run in a 2005-era runtime in 2026+

## Contributing

This is a fresh / open playground for unusual ideas. Welcome:

- ActionScript prototypes (math kernels, layer stubs)  
- Ideas on accelerating ops with Flash features (Pixel Bender remnants? Bitmap tricks?)  
- Ruffle compatibility reports  
- Model conversion sketches  
- Historical context on Flash's vector/3D capabilities for compute

Open an issue or PR with even tiny pieces — happy to discuss feasibility.

## Related Projects & Inspirations

- [Ruffle](https://ruffle.rs/) – Flash Player reimplementation in Rust + WebAssembly  
- [Lightspark](https://lightspark.github.io/) – Alternative Flash runtime  
- TensorFlow.js / ONNX Runtime Web (for comparison: modern browser ML)  
- Retro ML hacks (neural nets on NES, Commodore 64, etc.)

## License

(Recommend adding one — MIT is great for experimental/open projects)

→ Add via GitHub → "Add file" → choose MIT License

---

**SENTINAL**: Tomorrow's intelligence, yesterday's runtime.
