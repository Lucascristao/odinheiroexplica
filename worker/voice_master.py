"""Level planning and cautious pitch diagnostics; raw scene WAVs are never rewritten."""
import math
import numpy as np


def active_rms(samples,rate):
    samples=np.asarray(samples,dtype=float)
    window=max(1,round(rate*.02))
    padded=np.pad(samples,(0,(-len(samples))%window))
    energy=np.mean(padded.reshape(-1,window)**2,axis=1)
    active=energy[energy>10**(-45/10)]
    return 10*math.log10(float(active.mean())) if len(active) else None


def level_plan(activities, target_dbfs=-18.0, peak_ceiling=.975):
    records=[]
    ceiling_db=20*math.log10(peak_ceiling)
    for activity in activities:
        rms=activity.get("active_rms_dbfs", activity.get("rms_dbfs"))
        peak=activity.get("sample_peak_dbfs")
        if not isinstance(rms,(float,int)) or not math.isfinite(rms) or rms < -60 or not isinstance(peak,(float,int)) or not math.isfinite(peak):
            raise ValueError("Equalização exige energia de fala ativa e pico medidos.")
        records.append((float(rms),float(peak)))
    # One shared attainable target avoids a peak-limited scene changing volume.
    common=min([target_dbfs]+[rms+ceiling_db-peak for rms,peak in records])
    if common < -24:
        raise ValueError("Pico/energia vocal impedem nível comum adequado; revise a cena, sem comprimir o WAV bruto.")
    return {"method":"active-speech-rms-shared-target-v1", "requested_dbfs":target_dbfs,"target_dbfs":round(common,4),"peak_ceiling":peak_ceiling,"scenes":[{"gain":10**((common-rms)/20),"gain_db":round(common-rms,4),"raw_active_rms_dbfs":rms,"expected_active_rms_dbfs":round(common,4),"expected_peak_dbfs":round(peak+common-rms,4)} for rms,peak in records]}


def pitch_summary(samples, rate):
    """Autocorrelation estimates; consonants, creaky voice and octaves limit interpretation."""
    samples=np.asarray(samples,dtype=float)
    size=round(rate*.04)
    low,high=round(rate/350),round(rate/70)
    values=[]
    for start in range(0,len(samples)-size,max(1,round(rate*.08))):
        part=samples[start:start+size]
        part=part-part.mean()
        if np.sqrt(np.mean(part**2)) < 10**(-40/20):
            continue
        spectrum=np.fft.rfft(part,n=2**int(math.ceil(math.log2(size*2))))
        corr=np.fft.irfft(spectrum*np.conj(spectrum))[:size]
        if corr[0]<=0:
            continue
        corr=corr/corr[0]
        peaks=[i for i in range(low+1,min(high,size-1)) if corr[i]>corr[i-1] and corr[i]>=corr[i+1] and corr[i]>=.6]
        if not peaks:
            continue
        best=max(corr[i] for i in peaks)
        lag=next(i for i in peaks if corr[i]>=best*.9)
        values.append((start/rate,rate/lag))
    duration=len(samples)/rate
    def median(part):
        return round(float(np.median(part)),2) if len(part)>=8 else None
    return {"method":"autocorrelation-40ms-80ms-hop-70to350hz", "voiced_windows":len(values),"median_hz":median([v for _,v in values]),"opening_hz":median([v for t,v in values if t<4]),"closing_hz":median([v for t,v in values if t>duration-4]),"scope":"Estimate only: intonation, octave errors and voice quality require listening. No pitch correction applied."}
