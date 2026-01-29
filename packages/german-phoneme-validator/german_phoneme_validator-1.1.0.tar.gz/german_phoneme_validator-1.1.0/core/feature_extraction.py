"""
Feature extraction functions for audio processing.
Extracted from utils/dl_data_preparation.py for standalone use.
"""

from pathlib import Path
import numpy as np
import librosa
from scipy import signal
import warnings

# Try to import optional libraries
try:
    import parselmouth
    HAS_PARSELMOUTH = True
except ImportError:
    HAS_PARSELMOUTH = False

try:
    import webrtcvad
    HAS_WEBRTCVAD = True
except ImportError:
    HAS_WEBRTCVAD = False

# ============================================================================
# CONSTANTS
# ============================================================================

SAMPLE_RATE = 16000
N_MELS = 128
HOP_LENGTH = 512
MFCC_N_COEFFS = 13
SPECTROGRAM_WINDOW_MS = 200  # For spectrograms (will be longer with context)

# Pre-emphasis filter coefficient for formant extraction
PRE_EMPHASIS_COEFF = 0.97

# Formant extraction parameters
FORMANTS_MIN_FREQ_HZ = 50  # Minimum frequency for formant detection (Hz)
FORMANTS_MAGNITUDE_THRESHOLD = 0.7  # Minimum magnitude threshold for formant filtering

# Burst detection frequency range (Hz)
BURST_DETECTION_LOW_FREQ_HZ = 2000  # Low frequency for burst detection
BURST_DETECTION_HIGH_FREQ_HZ = 8000  # High frequency for burst detection

# Voicing detection frequency range (Hz)
VOICING_DETECTION_LOW_FREQ_HZ = 50  # Low frequency for voicing detection
VOICING_DETECTION_HIGH_FREQ_HZ = 500  # High frequency for voicing detection

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _normalize_filter_frequencies(low_freq_hz, high_freq_hz, nyquist):
    """
    Normalize filter frequencies to [0, 1] range and ensure they're within valid bounds.
    
    Args:
        low_freq_hz: Low frequency in Hz
        high_freq_hz: High frequency in Hz
        nyquist: Nyquist frequency (sr / 2)
        
    Returns:
        Tuple of (normalized_low_freq, normalized_high_freq) in [0.01, 0.99] range
    """
    low_freq = low_freq_hz / nyquist
    high_freq = high_freq_hz / nyquist
    low_freq = max(0.01, min(low_freq, 0.99))
    high_freq = max(0.01, min(high_freq, 0.99))
    return low_freq, high_freq

# ============================================================================
# FEATURE EXTRACTION FUNCTIONS
# ============================================================================

def extract_mfcc_features(audio, sr=SAMPLE_RATE, n_mfcc=MFCC_N_COEFFS, hop_length=HOP_LENGTH):
    """Extract MFCC features and their deltas."""
    # Input validation
    if audio is None or len(audio) == 0:
        raise ValueError("Audio input cannot be empty")
    if sr <= 0:
        raise ValueError(f"Sample rate must be positive, got {sr}")
    
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc, hop_length=hop_length)
    
    # Handle short audio files: adjust delta width based on available frames
    n_frames = mfcc.shape[1]
    default_width = 9
    
    if n_frames < default_width:
        if n_frames < 3:
            calculated_width = 3
        elif n_frames < 9:
            calculated_width = n_frames if n_frames % 2 == 1 else n_frames - 1
            calculated_width = max(3, calculated_width)
        else:
            calculated_width = 9
        if calculated_width % 2 == 0:
            calculated_width = max(3, calculated_width - 1)
        delta_mfcc = librosa.feature.delta(mfcc, width=calculated_width, mode='nearest')
        delta2_mfcc = librosa.feature.delta(mfcc, order=2, width=calculated_width, mode='nearest')
    else:
        delta_mfcc = librosa.feature.delta(mfcc)
        delta2_mfcc = librosa.feature.delta(mfcc, order=2)
    
    return {
        'mfcc_mean': np.mean(mfcc, axis=1),
        'mfcc_std': np.std(mfcc, axis=1),
        'delta_mfcc_mean': np.mean(delta_mfcc, axis=1),
        'delta_mfcc_std': np.std(delta_mfcc, axis=1),
        'delta2_mfcc_mean': np.mean(delta2_mfcc, axis=1),
        'delta2_mfcc_std': np.std(delta2_mfcc, axis=1),
    }

def extract_energy_features(audio, sr=SAMPLE_RATE, hop_length=HOP_LENGTH):
    """Extract energy-related features."""
    rms = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
    zcr = librosa.feature.zero_crossing_rate(audio, hop_length=hop_length)[0]
    
    return {
        'energy_rms': np.mean(rms),
        'energy_rms_std': np.std(rms),
        'energy_zcr': np.mean(zcr),
        'energy_zcr_std': np.std(zcr),
    }

def extract_spectral_features(audio, sr=SAMPLE_RATE, hop_length=HOP_LENGTH):
    """Extract spectral features."""
    centroid = librosa.feature.spectral_centroid(y=audio, sr=sr, hop_length=hop_length)[0]
    rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr, hop_length=hop_length)[0]
    bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr, hop_length=hop_length)[0]
    contrast = librosa.feature.spectral_contrast(y=audio, sr=sr, hop_length=hop_length)
    
    return {
        'spectral_centroid': np.mean(centroid),
        'spectral_centroid_std': np.std(centroid),
        'spectral_rolloff': np.mean(rolloff),
        'spectral_rolloff_std': np.std(rolloff),
        'spectral_bandwidth': np.mean(bandwidth),
        'spectral_bandwidth_std': np.std(bandwidth),
        'spectral_contrast_mean': np.mean(contrast, axis=1),
    }

def extract_formants_lpc(audio, sr=SAMPLE_RATE, n_formants=4, order=10):
    """Extract formants using LPC (Linear Predictive Coding)."""
    # Pre-emphasis filter
    audio_pre = signal.lfilter([1, -PRE_EMPHASIS_COEFF], 1, audio)
    
    # Frame the signal
    frame_length = int(0.025 * sr)  # 25ms frames
    hop_length_frame = int(0.010 * sr)  # 10ms hop
    
    formants_list = []
    
    for i in range(0, len(audio_pre) - frame_length, hop_length_frame):
        frame = audio_pre[i:i+frame_length]
        windowed = frame * signal.windows.hann(len(frame))
        
        try:
            # Compute autocorrelation
            autocorr = np.correlate(windowed, windowed, mode='full')
            autocorr = autocorr[len(autocorr)//2:len(autocorr)//2+order+1]
            
            # Levinson-Durbin recursion
            a = np.zeros(order + 1)
            a[0] = 1.0
            e = autocorr[0]
            
            for j in range(1, order + 1):
                k = -np.sum(a[:j] * autocorr[j:0:-1]) / e
                a[1:j+1] = a[1:j+1] + k * a[j-1::-1]
                a[j] = k
                e = e * (1 - k * k)
            
            roots = np.roots(a)
            roots = roots[np.imag(roots) >= 0]
            angles = np.angle(roots)
            freqs = angles * (sr / (2 * np.pi))
            magnitudes = np.abs(roots)
            
            # Filter: formants should have high magnitude and be in valid frequency range
            freq_mag_pairs = [(f, m) for f, m in zip(freqs, magnitudes) 
                              if FORMANTS_MIN_FREQ_HZ < f < sr/2 and m > FORMANTS_MAGNITUDE_THRESHOLD]
            freq_mag_pairs.sort(key=lambda x: x[1], reverse=True)
            freqs = [f for f, m in freq_mag_pairs]
            
            formants = freqs[:n_formants]
            while len(formants) < n_formants:
                formants.append(0.0)
            
            formants_list.append(formants[:n_formants])
        except Exception:
            formants_list.append([0.0] * n_formants)
    
    if len(formants_list) == 0:
        return {
            'formant_f1': 0.0, 'formant_f2': 0.0, 'formant_f3': 0.0, 'formant_f4': 0.0,
            'formant_f1_std': 0.0, 'formant_f2_std': 0.0, 'formant_f3_std': 0.0, 'formant_f4_std': 0.0,
        }
    
    formants_array = np.array(formants_list)
    
    return {
        'formant_f1': np.mean(formants_array[:, 0]) if len(formants_array) > 0 and np.any(formants_array[:, 0] > 0) else 0.0,
        'formant_f2': np.mean(formants_array[:, 1]) if len(formants_array) > 0 and np.any(formants_array[:, 1] > 0) else 0.0,
        'formant_f3': np.mean(formants_array[:, 2]) if len(formants_array) > 0 and np.any(formants_array[:, 2] > 0) else 0.0,
        'formant_f4': np.mean(formants_array[:, 3]) if len(formants_array) > 0 and np.any(formants_array[:, 3] > 0) else 0.0,
        'formant_f1_std': np.std(formants_array[:, 0]) if len(formants_array) > 0 and np.any(formants_array[:, 0] > 0) else 0.0,
        'formant_f2_std': np.std(formants_array[:, 1]) if len(formants_array) > 0 and np.any(formants_array[:, 1] > 0) else 0.0,
        'formant_f3_std': np.std(formants_array[:, 2]) if len(formants_array) > 0 and np.any(formants_array[:, 2] > 0) else 0.0,
        'formant_f4_std': np.std(formants_array[:, 3]) if len(formants_array) > 0 and np.any(formants_array[:, 3] > 0) else 0.0,
    }

def extract_formants_parselmouth(audio, sr=SAMPLE_RATE, n_formants=4):
    """Extract formants using Parselmouth (Praat)."""
    if not HAS_PARSELMOUTH:
        return extract_formants_lpc(audio, sr, n_formants)
    
    try:
        sound = parselmouth.Sound(audio, sampling_frequency=sr)
        formant = sound.to_formant_burg(time_step=0.01)
        
        formants_list = []
        times = np.arange(0, sound.duration, 0.01)
        
        for t in times:
            formants = []
            for i in range(1, n_formants + 1):
                try:
                    f = formant.get_value_at_time(i, t)
                    if f > 0:
                        formants.append(f)
                    else:
                        formants.append(0.0)
                except:
                    formants.append(0.0)
            formants_list.append(formants)
        
        formants_array = np.array(formants_list)
        
        return {
            'formant_f1': np.mean(formants_array[:, 0]) if len(formants_array) > 0 and np.any(formants_array[:, 0] > 0) else 0.0,
            'formant_f2': np.mean(formants_array[:, 1]) if len(formants_array) > 0 and np.any(formants_array[:, 1] > 0) else 0.0,
            'formant_f3': np.mean(formants_array[:, 2]) if len(formants_array) > 0 and np.any(formants_array[:, 2] > 0) else 0.0,
            'formant_f4': np.mean(formants_array[:, 3]) if len(formants_array) > 0 and np.any(formants_array[:, 3] > 0) else 0.0,
            'formant_f1_std': np.std(formants_array[:, 0]) if len(formants_array) > 0 and np.any(formants_array[:, 0] > 0) else 0.0,
            'formant_f2_std': np.std(formants_array[:, 1]) if len(formants_array) > 0 and np.any(formants_array[:, 1] > 0) else 0.0,
            'formant_f3_std': np.std(formants_array[:, 2]) if len(formants_array) > 0 and np.any(formants_array[:, 2] > 0) else 0.0,
            'formant_f4_std': np.std(formants_array[:, 3]) if len(formants_array) > 0 and np.any(formants_array[:, 3] > 0) else 0.0,
        }
    except Exception as e:
        return extract_formants_lpc(audio, sr, n_formants)

def extract_quality_metrics(audio, sr=SAMPLE_RATE, hop_length=HOP_LENGTH):
    """Extract quality metrics for noise assessment."""
    stft = librosa.stft(audio, hop_length=hop_length)
    magnitude = np.abs(stft)
    magnitude = magnitude + 1e-10
    
    geometric_mean = np.exp(np.mean(np.log(magnitude), axis=0))
    arithmetic_mean = np.mean(magnitude, axis=0)
    spectral_flatness = geometric_mean / (arithmetic_mean + 1e-10)
    spectral_flatness_mean = np.mean(spectral_flatness)
    
    harmonic = librosa.effects.harmonic(audio)
    percussive = librosa.effects.percussive(audio)
    hnr = np.mean(harmonic**2) / (np.mean(percussive**2) + 1e-10)
    
    zcr = librosa.feature.zero_crossing_rate(audio, hop_length=hop_length)[0]
    zcr_mean = np.mean(zcr)
    
    rms = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
    energy_std = np.std(rms)
    energy_mean = np.mean(rms)
    energy_cv = energy_std / (energy_mean + 1e-10)
    
    return {
        'spectral_flatness': spectral_flatness_mean,
        'harmonic_noise_ratio': hnr,
        'zcr_mean': zcr_mean,
        'energy_cv': energy_cv,
    }

def detect_burst(audio, sr=SAMPLE_RATE):
    """
    Detect the moment of plosive burst through high-frequency energy analysis.
    
    Returns:
        burst_time_ms: Time of burst in milliseconds (relative to audio start)
        burst_confidence: Confidence score (0-1)
    """
    try:
        # High-frequency filtering for burst detection (2-8 kHz)
        nyquist = sr / 2
        low_freq, high_freq = _normalize_filter_frequencies(
            BURST_DETECTION_LOW_FREQ_HZ, BURST_DETECTION_HIGH_FREQ_HZ, nyquist
        )
        
        b, a = signal.butter(4, [low_freq, high_freq], btype='band')
        audio_hf = signal.filtfilt(b, a, audio)
        
        # Compute energy envelope
        frame_length = int(0.01 * sr)  # 10ms frames
        hop_length = int(0.005 * sr)   # 5ms hop
        
        energy = []
        for i in range(0, len(audio_hf) - frame_length, hop_length):
            frame = audio_hf[i:i+frame_length]
            energy.append(np.mean(frame**2))
        
        if len(energy) == 0:
            return 0.0, 0.0
        
        energy = np.array(energy)
        energy_normalized = (energy - energy.min()) / (energy.max() - energy.min() + 1e-10)
        
        # Search in first half of segment for burst
        search_end = len(energy) // 2
        if search_end < 3:
            search_end = len(energy)
        
        # Find peak with sharp rise
        peak_idx = np.argmax(energy_normalized[:search_end])
        
        # Check for sharp rise before peak
        if peak_idx > 0:
            rise = energy_normalized[peak_idx] - energy_normalized[max(0, peak_idx-3)]
            confidence = min(1.0, rise * 2.0)  # Normalize confidence
        else:
            confidence = 0.5
        
        # Convert to time in milliseconds
        burst_time_ms = (peak_idx * hop_length / sr) * 1000
        
        return float(burst_time_ms), float(confidence)
    except Exception as e:
        return 0.0, 0.0

def _detect_periodicity_peaks(audio_segment, sr=SAMPLE_RATE):
    """
    Detect periodicity peaks in audio segment using autocorrelation.
    
    Args:
        audio_segment: Audio segment to analyze
        sr: Sample rate
        
    Returns:
        List of (peak_value, peak_index) tuples
    """
    frame_length = int(0.025 * sr)  # 25ms frames
    hop_length = int(0.01 * sr)     # 10ms hop
    
    autocorr_peaks = []
    for i in range(0, len(audio_segment) - frame_length, hop_length):
        frame = audio_segment[i:i+frame_length]
        frame = frame * signal.windows.hann(len(frame))
        
        # Autocorrelation
        autocorr = np.correlate(frame, frame, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        
        # Find first significant peak (periodicity)
        min_period = int(2 / 1000 * sr)  # 2ms
        max_period = int(20 / 1000 * sr)  # 20ms
        
        if len(autocorr) > max_period:
            search_range = autocorr[min_period:max_period]
            if len(search_range) > 0:
                peak_val = np.max(search_range)
                peak_idx = np.argmax(search_range) + min_period
                autocorr_peaks.append((peak_val, peak_idx))
    
    return autocorr_peaks

def detect_voicing_onset(audio, sr=SAMPLE_RATE, burst_time_ms=None):
    """
    Detect the onset of voicing through low-frequency energy and autocorrelation.
    
    Returns:
        voicing_onset_ms: Time of voicing onset in milliseconds
        voicing_confidence: Confidence score (0-1)
    """
    try:
        # Low-frequency filtering for voicing (50-500 Hz)
        nyquist = sr / 2
        low_freq, high_freq = _normalize_filter_frequencies(
            VOICING_DETECTION_LOW_FREQ_HZ, VOICING_DETECTION_HIGH_FREQ_HZ, nyquist
        )
        
        b, a = signal.butter(4, [low_freq, high_freq], btype='band')
        audio_lf = signal.filtfilt(b, a, audio)
        
        # If burst_time is provided, search after burst
        if burst_time_ms is not None:
            burst_samples = int(burst_time_ms / 1000 * sr)
            search_start = max(0, burst_samples)
        else:
            search_start = len(audio_lf) // 4  # Start from 25% of signal
        
        search_audio = audio_lf[search_start:]
        
        if len(search_audio) < int(0.05 * sr):  # Need at least 50ms
            return float(len(audio) / sr * 1000), 0.0
        
        # Frame-based autocorrelation for periodicity detection
        autocorr_peaks = _detect_periodicity_peaks(search_audio, sr)
        
        if len(autocorr_peaks) == 0:
            return float(len(audio) / sr * 1000), 0.0
        
        # Find first stable period (consistent peaks)
        if len(autocorr_peaks) >= 3:
            peak_values = [p[0] for p in autocorr_peaks[:5]]
            if np.std(peak_values) / (np.mean(peak_values) + 1e-10) < 0.5:
                voicing_onset_samples = search_start
                voicing_onset_ms = (voicing_onset_samples / sr) * 1000
                confidence = min(1.0, np.mean(peak_values) * 10.0)
                return float(voicing_onset_ms), float(confidence)
        
        # Fallback: use energy-based detection
        energy = librosa.feature.rms(y=search_audio, hop_length=hop_length)[0]
        energy_threshold = np.percentile(energy, 75)
        onset_idx = np.where(energy > energy_threshold)[0]
        
        if len(onset_idx) > 0:
            voicing_onset_samples = search_start + onset_idx[0] * hop_length
            voicing_onset_ms = (voicing_onset_samples / sr) * 1000
            return float(voicing_onset_ms), 0.7
        else:
            return float(len(audio) / sr * 1000), 0.0
            
    except Exception as e:
        return float(len(audio) / sr * 1000) if len(audio) > 0 else 0.0, 0.0

def extract_vot(audio, sr=SAMPLE_RATE):
    """
    Extract Voice Onset Time (VOT) - time between burst and voicing onset.
    
    Returns:
        Dictionary with VOT features
    """
    try:
        burst_time_ms, burst_conf = detect_burst(audio, sr)
        voicing_onset_ms, voicing_conf = detect_voicing_onset(audio, sr, burst_time_ms)
        
        vot_ms = voicing_onset_ms - burst_time_ms
        
        # Categorize VOT
        if vot_ms > 20:
            vot_category = 'positive'
        elif vot_ms < -20:
            vot_category = 'negative'
        else:
            vot_category = 'zero'
        
        return dict(
            vot_ms=float(vot_ms),
            burst_time_ms=float(burst_time_ms),
            voicing_onset_ms=float(voicing_onset_ms),
            burst_confidence=float(burst_conf),
            voicing_confidence=float(voicing_conf),
            vot_category=vot_category
        )
    except Exception as e:
        return dict(
            vot_ms=0.0,
            burst_time_ms=0.0,
            voicing_onset_ms=0.0,
            burst_confidence=0.0,
            voicing_confidence=0.0,
            vot_category='zero'
        )

def extract_zcr_around_burst(audio, sr=SAMPLE_RATE, burst_time_ms=None, hop_length=HOP_LENGTH):
    """Extract Zero Crossing Rate around burst moment."""
    try:
        if burst_time_ms is None:
            burst_time_ms, _ = detect_burst(audio, sr)
        
        # Window around burst: ±10ms
        window_ms = 10
        burst_samples = int(burst_time_ms / 1000 * sr)
        window_samples = int(window_ms / 1000 * sr)
        
        start_idx = max(0, burst_samples - window_samples)
        end_idx = min(len(audio), burst_samples + window_samples)
        
        if end_idx <= start_idx:
            return dict(
                zcr_burst_mean=0.0,
                zcr_burst_std=0.0,
                zcr_burst_max=0.0
            )
        
        burst_window = audio[start_idx:end_idx]
        zcr = librosa.feature.zero_crossing_rate(burst_window, hop_length=hop_length)[0]
        
        return dict(
            zcr_burst_mean=float(np.mean(zcr)),
            zcr_burst_std=float(np.std(zcr)),
            zcr_burst_max=float(np.max(zcr))
        )
    except Exception as e:
        return dict(
            zcr_burst_mean=0.0,
            zcr_burst_std=0.0,
            zcr_burst_max=0.0
        )

def extract_burst_spectral_centroid(audio, sr=SAMPLE_RATE, burst_time_ms=None, hop_length=HOP_LENGTH):
    """Extract spectral centroid around burst moment."""
    try:
        if burst_time_ms is None:
            burst_time_ms, _ = detect_burst(audio, sr)
        
        # Window around burst: ±5ms
        window_ms = 5
        burst_samples = int(burst_time_ms / 1000 * sr)
        window_samples = int(window_ms / 1000 * sr)
        
        start_idx = max(0, burst_samples - window_samples)
        end_idx = min(len(audio), burst_samples + window_samples)
        
        if end_idx <= start_idx:
            return dict(
                burst_spectral_centroid=0.0,
                burst_spectral_centroid_std=0.0,
                burst_spectral_centroid_max=0.0
            )
        
        burst_window = audio[start_idx:end_idx]
        centroid = librosa.feature.spectral_centroid(y=burst_window, sr=sr, hop_length=hop_length)[0]
        
        return dict(
            burst_spectral_centroid=float(np.mean(centroid)),
            burst_spectral_centroid_std=float(np.std(centroid)),
            burst_spectral_centroid_max=float(np.max(centroid))
        )
    except Exception as e:
        return dict(
            burst_spectral_centroid=0.0,
            burst_spectral_centroid_std=0.0,
            burst_spectral_centroid_max=0.0
        )

def extract_low_frequency_energy(audio, sr=SAMPLE_RATE, hop_length=HOP_LENGTH):
    """Extract low-frequency energy (50-500 Hz) characteristic of voicing."""
    try:
        # Low-frequency filtering (50-500 Hz)
        nyquist = sr / 2
        low_freq, high_freq = _normalize_filter_frequencies(
            VOICING_DETECTION_LOW_FREQ_HZ, VOICING_DETECTION_HIGH_FREQ_HZ, nyquist
        )
        
        b, a = signal.butter(4, [low_freq, high_freq], btype='band')
        audio_lf = signal.filtfilt(b, a, audio)
        
        # Compute energy
        rms_lf = librosa.feature.rms(y=audio_lf, hop_length=hop_length)[0]
        rms_total = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
        
        energy_lf_mean = np.mean(rms_lf)
        energy_lf_std = np.std(rms_lf)
        energy_total_mean = np.mean(rms_total)
        energy_ratio = energy_lf_mean / (energy_total_mean + 1e-10)
        
        return dict(
            low_freq_energy_mean=float(energy_lf_mean),
            low_freq_energy_std=float(energy_lf_std),
            low_freq_energy_ratio=float(energy_ratio)
        )
    except Exception as e:
        return dict(
            low_freq_energy_mean=0.0,
            low_freq_energy_std=0.0,
            low_freq_energy_ratio=0.0
        )

def validate_plosive_duration(audio, sr=SAMPLE_RATE, phoneme_type='b-p', duration_ms=None, hop_length=HOP_LENGTH):
    """
    Validate plosive duration (closure and burst lengths).
    
    Returns:
        Dictionary with validation flags and durations
    """
    try:
        # Parameters for b-p
        closure_min_ms = 20
        closure_max_ms = 100
        burst_min_ms = 5
        burst_max_ms = 30
        
        # Detect burst
        burst_time_ms, burst_conf = detect_burst(audio, sr)
        
        # Estimate closure duration (time before burst)
        closure_duration_ms = burst_time_ms
        
        # Estimate burst duration (short high-energy segment after burst)
        if burst_time_ms > 0:
            burst_samples = int(burst_time_ms / 1000 * sr)
            post_burst_window = audio[burst_samples:min(len(audio), burst_samples + int(0.05 * sr))]
            
            if len(post_burst_window) > 0:
                rms = librosa.feature.rms(y=post_burst_window, hop_length=hop_length)[0]
                peak_energy = np.max(rms)
                threshold = peak_energy * 0.3
                drop_idx = np.where(rms < threshold)[0]
                
                if len(drop_idx) > 0:
                    burst_duration_ms = (drop_idx[0] * hop_length / sr) * 1000
                else:
                    burst_duration_ms = min(30.0, len(post_burst_window) / sr * 1000)
            else:
                burst_duration_ms = 10.0
        else:
            burst_duration_ms = 0.0
        
        # Validation
        is_valid_closure = closure_min_ms <= closure_duration_ms <= closure_max_ms
        is_valid_burst = burst_min_ms <= burst_duration_ms <= burst_max_ms
        
        return dict(
            is_valid_closure=bool(is_valid_closure),
            is_valid_burst=bool(is_valid_burst),
            closure_duration_ms=float(closure_duration_ms),
            burst_duration_ms=float(burst_duration_ms)
        )
    except Exception as e:
        return dict(
            is_valid_closure=False,
            is_valid_burst=False,
            closure_duration_ms=0.0,
            burst_duration_ms=0.0
        )

def apply_vad(audio, sr=SAMPLE_RATE, hop_length=HOP_LENGTH):
    """Apply Voice Activity Detection (VAD) using webrtcvad if available."""
    try:
        if HAS_WEBRTCVAD:
            vad = webrtcvad.Vad(2)  # Aggressiveness mode 2 (0-3)
            
            # webrtcvad requires 10ms, 20ms, or 30ms frames at specific sample rates
            if sr != 16000:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
                sr = 16000
            
            frame_duration_ms = 10
            frame_length = int(sr * frame_duration_ms / 1000)
            
            # Convert to int16
            audio_int16 = (audio * 32767).astype(np.int16)
            
            # Process frames
            vad_frames = []
            for i in range(0, len(audio_int16) - frame_length, frame_length):
                frame = audio_int16[i:i+frame_length]
                if len(frame) == frame_length:
                    is_speech = vad.is_speech(frame.tobytes(), sr)
                    vad_frames.append(is_speech)
            
            if len(vad_frames) > 0:
                speech_ratio = np.mean(vad_frames)
                speech_frames = sum(vad_frames)
                total_frames = len(vad_frames)
            else:
                speech_ratio = 0.0
                speech_frames = 0
                total_frames = 0
        else:
            # Fallback: energy-based VAD
            rms = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
            energy_threshold = np.percentile(rms, 25)
            speech_frames = np.sum(rms > energy_threshold)
            total_frames = len(rms)
            speech_ratio = speech_frames / total_frames if total_frames > 0 else 0.0
        
        return dict(
            vad_speech_ratio=float(speech_ratio),
            vad_speech_frames=int(speech_frames) if 'speech_frames' in locals() else 0,
            vad_total_frames=int(total_frames) if 'total_frames' in locals() else len(rms) if not HAS_WEBRTCVAD else 0
        )
    except Exception as e:
        return dict(
            vad_speech_ratio=0.0,
            vad_speech_frames=0,
            vad_total_frames=0
        )

def _prepare_audio_input(audio_input, sr=SAMPLE_RATE):
    """
    Prepare audio input from file path or numpy array.
    
    Args:
        audio_input: Path to audio file (str/Path) or numpy array of audio samples
        sr: Sample rate
        
    Returns:
        Tuple of (audio_array, actual_sample_rate)
    """
    if isinstance(audio_input, (str, Path)):
        audio, _ = librosa.load(audio_input, sr=sr, mono=True)
    elif isinstance(audio_input, np.ndarray):
        audio = audio_input
        # Ensure correct sample rate (resample if needed)
        if sr != SAMPLE_RATE:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=SAMPLE_RATE)
            sr = SAMPLE_RATE
    else:
        raise ValueError(f"Unsupported audio_input type: {type(audio_input)}")
    
    # Validate audio array
    if audio is None or len(audio) == 0:
        raise ValueError("Audio input cannot be empty after loading")
    if sr <= 0:
        raise ValueError(f"Sample rate must be positive, got {sr}")
    
    return audio, sr

def extract_all_features(audio_input, sr=SAMPLE_RATE, phoneme_type='b-p', hop_length=HOP_LENGTH):
    """
    Extract all features from an audio file or numpy array.
    
    Args:
        audio_input: Path to audio file (str/Path) or numpy array of audio samples
        sr: Sample rate
        phoneme_type: Phoneme type for validation
        hop_length: Hop length for feature extraction
        
    Returns:
        Dictionary of features or None if error
    """
    try:
        # Prepare audio input (load and validate)
        audio, sr = _prepare_audio_input(audio_input, sr)
        
        features = {}
        features.update(extract_mfcc_features(audio, sr, hop_length=hop_length))
        features.update(extract_energy_features(audio, sr, hop_length=hop_length))
        features.update(extract_spectral_features(audio, sr, hop_length=hop_length))
        
        if HAS_PARSELMOUTH:
            features.update(extract_formants_parselmouth(audio, sr))
        else:
            features.update(extract_formants_lpc(audio, sr))
        
        features.update(extract_quality_metrics(audio, sr, hop_length=hop_length))
        
        # Extract VOT and burst features
        vot_features = extract_vot(audio, sr)
        features.update(vot_features)
        
        # Extract burst-specific features
        burst_time = vot_features.get('burst_time_ms', 0.0)
        features.update(extract_zcr_around_burst(audio, sr, burst_time, hop_length=hop_length))
        features.update(extract_burst_spectral_centroid(audio, sr, burst_time, hop_length=hop_length))
        
        # Extract low-frequency energy
        features.update(extract_low_frequency_energy(audio, sr, hop_length=hop_length))
        
        # Validate plosive duration
        duration_ms = len(audio) / sr * 1000
        validation = validate_plosive_duration(audio, sr, phoneme_type=phoneme_type, duration_ms=duration_ms, hop_length=hop_length)
        features.update(validation)
        
        # Apply VAD
        vad_features = apply_vad(audio, sr, hop_length=hop_length)
        features.update(vad_features)
        
        return features
    except Exception as e:
        return None

def extract_spectrogram_window(audio_input, target_duration_ms=SPECTROGRAM_WINDOW_MS, sr=SAMPLE_RATE, n_mels=N_MELS, hop_length=HOP_LENGTH):
    """
    Extract mel-spectrogram with fixed window size.
    
    Args:
        audio_input: Path to audio file (str/Path) or numpy array of audio samples
        target_duration_ms: Target duration in milliseconds
        sr: Sample rate
        n_mels: Number of mel bands
        hop_length: Hop length for spectrogram
        
    Returns:
        Mel-spectrogram in dB or None if error
    """
    try:
        # Prepare audio input (load and validate)
        audio, sr = _prepare_audio_input(audio_input, sr)
        
        audio_duration_ms = len(audio) / sr * 1000
        
        target_samples = int(target_duration_ms / 1000 * sr)
        
        if len(audio) < target_samples:
            padding = target_samples - len(audio)
            audio = np.pad(audio, (0, padding), mode='constant')
        elif len(audio) > target_samples:
            audio = audio[:target_samples]
        
        mel_spec = librosa.feature.melspectrogram(
            y=audio, 
            sr=sr, 
            n_mels=n_mels, 
            hop_length=hop_length,
            fmax=sr/2
        )
        
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        return mel_spec_db
    except Exception as e:
        return None

