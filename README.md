Toy-Physical-Layer-Key-Exchange-PLKE-Simulation




This is a simple Python script to simulate the core concept of **Physical Layer Key Exchange (PLKE)**.

It models how two parties, "Alice" and "Bob," can theoretically generate an identical secret key by measuring the unique "fingerprint" of their shared environment (in this case, a simulated room's impulse response), even in the presence of noise. The security is based on the idea that their shared channel is reciprocal, while an eavesdropper ("Eve") at a different physical location will have a completely different and uncorrelated channel.

---

How to Run

This script only requires `numpy` and `scipy`.

1.  **Install dependencies:**
    ```bash
    pip install numpy scipy
    ```

2.  **Run the script:**
    ```bash
    python plke_simulation.py
    ```
    *(Note: You may need to rename `plke_simulation.py` to match your script's filename.)*

---

Example Output

A successful run will show that Alice and Bob's initial random signals converge into a shared "null" signal, which they then use to generate matching keys. Eve, however, fails to generate the same key.

```bash
Initial A/B corr: -0.093 (random, <0.1 = independent)
A[0:5]: [ 0.49671415 -0.1382643   0.64768854  1.52302986 -0.23415337] | B[0:5]: [-0.43380443  1.20303737 -0.96506568  0.26112276 -0.01775791] (distinct)
Stopped at iter 16, norm=0.963
Final norm: 0.963 (near-null = shared fingerprint)
Norm trend: [11.08298710325026, 9.77490695123992, 8.59972822137156, 7.545196323608625, 6.600000859508821]...[1.4429712686120532, 1.2858562304910915, 1.1511993202613175, 1.036683511874744, 0.9632822280735315] (drops ~90%)
Raw A/B bit corr: 0.957
Mismatches dropped: 2 (2.0%)
Keys match: True (A: 409b69a3, B: 409b69a3)
Eve corr with A: -0.023 (near 0 = obfuscated)

Theory Check: Independent starts → shared null → matching keys. Eve lost in echoes.
```

---

How It Works

The simulation runs in four main steps:

1.  **Setup (The "Room")**: We define a shared "Room Impulse Response" (`rir`) that represents the unique, complex echo pattern of a physical space. We also generate two independent, random "probe" signals (`A` and `B`) for Alice and Bob.

2.  **Iterative Exchange (The "Nulling")**: This is the core of the protocol.
    * Alice and Bob send their probes through the channel (convolution with `rir` + noise).
    * They each create a new signal by mixing their original probe with an *inverted* version of the signal they just received.
    * They exchange these new signals, and the process repeats.
    * Because their channel is reciprocal (identical), this iterative feedback loop causes their *received* signals (`REF_A` and `REF_B`) to converge and become nearly identical. They have "nulled" their differences, leaving only a shared signal derived from the channel itself.

3.  **Key Generation (The "Bits")**:
    * **Quantization:** Alice and Bob convert their final, near-identical analog signals into digital bits (1 if `> 0`, 0 otherwise).
    * **Reconciliation:** Due to noise, a few bits might not match. This script uses a toy method where they simply *drop* any mismatched bits.
    * **Hashing:** The final, identical bitstreams are hashed (`SHA-256`) to create a secure, fixed-length cryptographic key.

4.  **Eve Test**: We simulate an eavesdropper, Eve, who is at a different location. This is modeled by giving her a *different* impulse response (`eve_rir`). Because her channel is uncorrelated with the Alice-Bob channel, her resulting bits are random and do not match the generated key.

---

## A Note: "Toy" vs. "Real-World"

This is a **toy model** that demonstrates the concept in an *idealized* scenario. It is **not** a secure system as-is.

In the real world, this protocol faces several major challenges that are active areas of research:

* **Channel Reciprocity:** The script assumes the channel `A -> B` is identical to `B -> A`. In reality, speaker and microphone hardware are not identical, meaning the end-to-end channel is *not* perfectly reciprocal.
* **Authentication:** This protocol is vulnerable to a **Man-in-the-Middle (MITM) attack**. An active attacker could impersonate Bob to Alice and Alice to Bob, establishing separate keys with each and silently relaying/reading all messages.
* **Channel Stability:** The script assumes a static `rir`. Real acoustic environments are constantly changing (a person moving, a door opening), which would "de-cohere" the channel and break the key generation loop.

This simulation was created to explore the concept, not to be a secure implementation.
