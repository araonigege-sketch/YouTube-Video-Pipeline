import sys, wave
from pocketsphinx import Decoder
d = Decoder(samprate=16000)
with wave.open(sys.argv[1]) as w: data = w.readframes(w.getnframes())
out=[]
step = 16000*2*20  # 20 s chunks
for k in range(0, len(data), step):
    d.start_utt(); d.process_raw(data[k:k+step], full_utt=True); d.end_utt()
    out.append(f"[{k//32000:>4}s] " + (d.hyp().hypstr if d.hyp() else ""))
print("\n".join(out))
