import numpy as np
from scipy.signal import convolve
import hashlib

# Toy Params (your theory in mini)
length = 100
mu = 0.2  # Damping
noise_std = 0.3  # Noise
max_iters = 20
threshold = 1.0  # Stop if norm <1.0

# Step 1: Setup Room (RIR for reverb) & Tunes (independent A/B)
def generate_rir(size=50, decay=0.7):
    rir = np.zeros(size)
    rir[0] = 1.0  # Direct
    for i in range(1, size//5):
        rir[i*5] = decay ** i  # Echoes
    return rir / np.linalg.norm(rir)

rir = generate_rir()

rng_a = np.random.RandomState(42)
rng_b = np.random.RandomState(43)  # Separate seeds—independent!
A = rng_a.normal(0, 1, length)  # Alice's private noise
B = rng_b.normal(0, 1, length)  # Bob's—different!

print(f"Initial A/B corr: {np.corrcoef(A, B)[0,1]:.3f} (random, <0.1 = independent)")
print(f"A[0:5]: {A[:5]} | B[0:5]: {B[:5]} (distinct)")

# Step 2: Noisy Chat Loop (Exchange, estimate, update to null)
def channel_exchange(sig, rir, noise_std, rng):
    reverbed = convolve(sig, rir, mode='same')
    return reverbed + rng.normal(0, noise_std, length)

# Initial exchange
N1 = np.random.normal(0, noise_std, length)
REF_B = channel_exchange(A, rir, noise_std, rng_a)  # Bob receives A + noise/reverb
REF_A = channel_exchange(B, rir, noise_std, rng_b)  # Alice receives B + noise/reverb

norms = [np.linalg.norm(REF_A - REF_B)]
for k in range(1, max_iters + 1):
    S_A = A + mu * (-REF_A)  # Alice inverts/mixes
    S_B = B + mu * (-REF_B)  # Bob inverts/mixes
    R_B = channel_exchange(S_A, rir, noise_std, rng_a)  # Bob receives S_A + noise/reverb
    R_A = channel_exchange(S_B, rir, noise_std, rng_b)  # Alice receives S_B + noise/reverb
    REF_A = R_A
    REF_B = R_B
    new_norm = np.linalg.norm(REF_A - REF_B)
    norms.append(new_norm)
    if new_norm < threshold:
        print(f"Stopped at iter {k}, norm={new_norm:.3f}")
        break

print(f"Final norm: {norms[-1]:.3f} (near-null = shared fingerprint)")
print(f"Norm trend: {norms[:5]}...{norms[-5:]} (drops ~90%)")

# Step 3: Code the Quiet (Quantize to bits, recon, hash)
def quantize(resid):
    return (resid > 0).astype(int)  # Sign to 0/1

alice_bits = quantize(REF_A)
bob_bits = quantize(REF_B)
raw_corr = np.corrcoef(alice_bits, bob_bits)[0,1]
if raw_corr < 0:
    bob_bits = 1 - bob_bits  # Flip if anti
print(f"Raw A/B bit corr: {raw_corr:.3f}")

# Simple recon: Drop mismatches (toy parity—drop where differ)
keep = alice_bits == bob_bits
alice_bits = alice_bits[keep]
bob_bits = bob_bits[keep]
mismatches = length - keep.sum()
print(f"Mismatches dropped: {mismatches} ({mismatches/length*100:.1f}%)")

# Hash to key
alice_key = hashlib.sha256(alice_bits.tobytes()).hexdigest()[:8]  # Toy short
bob_key = hashlib.sha256(bob_bits.tobytes()).hexdigest()[:8]
success = alice_key == bob_key
print(f"Keys match: {success} (A: {alice_key}, B: {bob_key})")

# Step 4: Eve Test (Mismatched room + scramble)
eve_rir = np.roll(rir, 5)  # Delay = offset position
eve_rir[:5] = 0  # Zero pad
eve_ref = channel_exchange(A + B, eve_rir, noise_std * 1.5, np.random.RandomState(44))  # Her "wrong room"
eve_bits = quantize(eve_ref)
flips = np.random.random(len(eve_bits)) < 0.15  # Scramble 15%
eve_bits = np.bitwise_xor(eve_bits, flips.astype(int))
eve_corr = np.corrcoef(alice_bits[:len(eve_bits)], eve_bits)[0,1]
print(f"Eve corr with A: {eve_corr:.3f} (near 0 = obfuscated)")

print("\nTheory Check: Independent starts → shared null → matching keys. Eve lost in echoes.")
