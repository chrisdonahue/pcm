---
title: "Chapter 17: Computer Music Horizons"
---

# Computer Music Horizons

Congratulations on making it to the end of your journey with _Principles of Computer Music_!

In the first half of this book, we went in depth into the core _foundations_ of computer music: how sound is represented on a computer, its fundamental physical and mathematical properties, and how to efficiently synthesize and manipulate it in time and frequency. In the second half, we explored many different _topics_ in less detail, building on this common foundation, from physical modeling to effects, compression, and music AI.

For readers interested in continuing their study of computer music, where should you go from here? There are many possible directions! In this last chapter, we close with pointers to different engineering, creative, and research horizons in computer music.

### Application development

If you're interested in developing real-time audio applications, such as plugins for DAWs, web apps, game audio, or hardware instruments, here are some places to start. A good first read is Ross Bencina's classic post [_Real-time audio programming 101: time waits for nothing_](http://www.rossbencina.com/code/real-time-audio-programming-101-time-waits-for-nothing), which explains why audio code that runs one block at a time must never stall.

- **Plugins.** Most DAWs host plugins in Steinberg's [VST](https://www.steinberg.net/developers/) format or Apple's [Audio Unit](https://developer.apple.com/documentation/audiotoolbox/audio-unit-v3-plug-ins) (AU) format. The C++ framework [JUCE](https://juce.com) builds plugins in both formats, and standalone apps, from a single codebase.
- **Web audio.** The [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API) brings real-time audio to the browser, and its [AudioWorklet](https://developer.mozilla.org/en-US/docs/Web/API/AudioWorklet) interface lets you write your own processing, sample by sample. [Tone.js](https://tonejs.github.io) is a higher-level library for making music in the browser, and the [Web MIDI API](https://developer.mozilla.org/en-US/docs/Web/API/Web_MIDI_API) connects the browser to MIDI controllers.
- **Game audio.** Games typically use audio middleware such as [Wwise](https://www.audiokinetic.com/en/wwise/overview/) and [FMOD](https://www.fmod.com). Unreal Engine has its own procedural audio system, [MetaSounds](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-in-unreal-engine).
- **Mobile.** [AudioKit](https://www.audiokit.io) for iOS and macOS, and [Oboe](https://github.com/google/oboe) for Android.
- **Embedded hardware.** [Bela](https://bela.io), [Daisy](https://daisy.audio), and the [Teensy Audio Library](https://www.pjrc.com/teensy/td_libs_Audio.html) run audio code on small boards, for building your own instruments and effects pedals.
- **Python.** To keep working in Python, try [librosa](https://librosa.org) for audio analysis, [pedalboard](https://spotify.github.io/pedalboard/) for audio effects, [torchaudio](https://pytorch.org/audio/) for audio with PyTorch, and [pretty_midi](https://github.com/craffel/pretty-midi) and [music21](https://web.mit.edu/music21/) for symbolic music.
- **Community.** The [Audio Developer Conference](https://audio.dev) (ADC) is an annual conference for audio software developers.

### Creative practice

If you're interested in creating computer music, there are many environments to explore beyond Python. Many of them are built on the same ideas that we studied in this book, such as unit generators ([Chapter 4](../04-score-timbre)) and block-based processing.

- **Patching.** In these visual environments, you connect boxes (unit generators) with patch cords: [Max/MSP](https://cycling74.com/products/max), its open-source cousin [Pure Data](https://puredata.info) (Pd), and [VCV Rack](https://vcvrack.com), a simulator of modular synthesizers.
- **Live coding.** Live coders perform music by writing code in front of an audience, in languages such as [SuperCollider](https://supercollider.github.io), [TidalCycles](https://tidalcycles.org), [Strudel](https://strudel.cc) (a JavaScript port of TidalCycles that runs in the browser), [Sonic Pi](https://sonic-pi.net), and [ChucK](https://chuck.stanford.edu). [TOPLAP](https://toplap.org) and [Algorave](https://algorave.com) are communities of live coders.
- **Other languages.** [Csound](https://csound.com), a descendant of Max Mathews's original MUSIC-N languages, Roger Dannenberg's [Nyquist](https://www.cs.cmu.edu/~music/nyquist/), which inspired `pyquist`, [Faust](https://faust.grame.fr), a functional language for signal processing that compiles to plugins, web apps, and embedded hardware, and [p5.sound](https://p5js.org/reference/p5.sound/), for creative coding in the browser.
- **DAWs.** [Ableton Live](https://www.ableton.com/en/live/), [Logic Pro](https://www.apple.com/logic-pro/), [REAPER](https://www.reaper.fm), [Pro Tools](https://www.avid.com/pro-tools), [Bitwig Studio](https://www.bitwig.com), and the open-source [Ardour](https://ardour.org).
- **Music notation.** [MuseScore](https://musescore.org) and [LilyPond](https://lilypond.org), which typeset some of the scores in this book.

### Research conferences and societies

If you're interested in getting involved in computer music research, conferences and journals are where new research appears. A great way to figure out which community you're drawn to is to scan through the proceedings (or award-winning papers, if applicable) of the latest edition of each conference.

- **Music AI.** The [International Society for Music Information Retrieval](https://ismir.net) (ISMIR) conference and its journal [TISMIR](https://transactions.ismir.net), the machine learning conferences [ICLR](https://iclr.cc), [ICML](https://icml.cc), and [NeurIPS](https://neurips.cc), and the [AI Music Creativity](https://aimusiccreativity.org) conference (AIMC). For a reading list of recent research, see the end of [Chapter 16](../16-music-ai).
- **Signal processing.** [ICASSP](https://2026.ieeeicassp.org), [WASPAA](https://www.waspaa.com), [EUSIPCO](https://eurasip.org/eusipco-conferences/), the [International Conference on Digital Audio Effects](https://www.dafx.de) (DAFx), and the journal [_IEEE Transactions on Audio, Speech, and Language Processing_](https://signalprocessingsociety.org/publications-resources/ieee-transactions-audio-speech-and-language-processing).
- **Computer music.** The [International Computer Music Conference](https://www.computermusic.org) (ICMC), the Sound and Music Computing Conference (SMC), and the journals [_Computer Music Journal_](https://direct.mit.edu/comj) (CMJ), and [_Journal of New Music Research_](https://www.tandfonline.com/journals/nnmr20) (JNMR).
- **Interfaces.** [New Interfaces for Musical Expression](https://www.nime.org) (NIME), and the human-computer interaction conferences [IUI](https://iui.acm.org), [UIST](https://uist.acm.org), and [CHI](https://chi.acm.org).
- **Acoustics and audio engineering.** The [Acoustical Society of America](https://acousticalsociety.org) (ASA) and the [Audio Engineering Society](https://www.aes.org) (AES), and their journals.
- **Music perception and cognition.** The [Society for Music Perception and Cognition](https://www.musicperception.org) (SMPC/ICMPC), and the journal [_Music Perception_](https://online.ucpress.edu/mp).

### Academic hubs

If you're interested in academic study or research in computer music, here are some universities and institutes with active groups. In the US, several universities have dedicated programs or centers for music technology:

- [CMU Music and Technology](https://www.cmu.edu/cfa/music/programs/music-technology/)
- [UCSD MUSAIC](https://musaic.ucsd.edu)
- [MIT Music Technology](https://musictech.mit.edu)
- [NYU Music and Audio Research Laboratory](https://steinhardt.nyu.edu/marl) (MARL)
- [Georgia Tech Center for Music Technology](https://gtcmt.gatech.edu)
- [Stanford Center for Computer Research in Music and Acoustics](https://ccrma.stanford.edu) (CCRMA)
- [UCSB Media Arts and Technology](https://www.mat.ucsb.edu)

Other US universities have individual faculty members who lead research groups in computer music and music AI:

- Northwestern Computer Science ([Bryan Pardo](https://interactiveaudiolab.github.io))
- Cornell Computer Science ([John Thickstun](https://johnthickstun.com))
- Michigan Performing Arts Technology ([Hao-Wen Dong](https://hermandong.com))
- Dartmouth Computer Science ([Nikhil Singh](https://www.sahaslab.com))
- Rochester Electrical and Computer Engineering ([Zhiyao Duan](https://labsites.rochester.edu/air/))
- University of Washington Information School ([Jin Ha Lee](https://ischool.uw.edu/people/faculty/profile/jinhalee)) and Computer Science ([Noah A. Smith](https://nasmith.github.io))
- NJIT Informatics ([Mark Cartwright](https://sinc-lab.com))

Outside of the US:

- JKU Linz, [Institute of Computational Perception](https://www.jku.at/en/institute-of-computational-perception/)
- McGill, [Music Technology Area](https://www.mcgill.ca/music/about-us/music-technology) and [CIRMMT](https://www.cirmmt.org/en)
- FAU Erlangen, [International Audio Laboratories Erlangen](https://www.audiolabs-erlangen.de)
- UPF Barcelona, [Music Technology Group](https://www.upf.edu/web/mtg)
- [IRCAM](https://www.ircam.fr/en), Paris
- AIST, Japan ([Masataka Goto](https://staff.aist.go.jp/m.goto/))
- KAIST, [Music and Audio Computing Lab](https://mac.kaist.ac.kr)
- Seoul National University, [Music and Audio Research Group](https://snu-marg.notion.site)
- Sogang University, [MALer Lab](https://malerlab.github.io)
- TU Delft, [Multimedia Computing Group](https://www.tudelft.nl/en/ewi/over-de-faculteit/afdelingen/intelligent-systems/multimedia-computing)
- KTH, [Speech, Music and Hearing](https://www.kth.se/tmh/)
- SUTD, [AMAAI Lab](https://amaai-lab.github.io)
- National Taiwan University, [Music and AI Lab](https://affige.github.io/lab.html)
- MBZUAI, [Music X Lab](https://www.musicxlab.com)
- Queen Mary University of London, [Centre for Digital Music](https://c4dm.eecs.qmul.ac.uk) (C4DM)
- Aalto University, [Aalto Acoustics Lab](https://www.aalto.fi/en/aalto-acoustics-lab)
- Goldsmiths, University of London, [Electronic Music Studios](https://sites.gold.ac.uk/electronic-music-studios/)
- University of Oslo, [RITMO](https://www.uio.no/ritmo/english/)
- Ghent University, [IPEM](https://www.ugent.be/lw/kunstwetenschappen/ipem/en)

This is likely an incomplete list, and will naturally become dated over time. For many more, see ISMIR's list of [research centers](https://ismir.net/resources/research-centers/).

### Textbooks and courses

If you're interested in going deeper into the topics of this book, here are some textbooks to read next, several of which are freely available online.

- **Computer music.** Roger Dannenberg's _Introduction to Computer Music_ {cite}`dannenberg2024intro`, Curtis Roads's _The Computer Music Tutorial_ {cite}`roads2023computer`, Miller Puckette's [_The Theory and Technique of Electronic Music_](https://msp.ucsd.edu/techniques/latest/book.pdf) {cite}`puckette2007theory`, Charles Dodge and Thomas Jerse's _Computer Music_ {cite}`dodge1997computer`, and F. Richard Moore's _Elements of Computer Music_ {cite}`moore1990elements`.
- **Signal processing.** Brian McFee's [_Digital Signals Theory_](https://brianmcfee.net/dstbook-site/) {cite}`mcfee2023digital`, and Julius O. Smith III's four books: [_Mathematics of the Discrete Fourier Transform_](https://ccrma.stanford.edu/~jos/mdft/) {cite}`smith2007mathematics`, [_Introduction to Digital Filters_](https://ccrma.stanford.edu/~jos/filters/) {cite}`smith2007introduction`, [_Physical Audio Signal Processing_](https://ccrma.stanford.edu/~jos/pasp/) {cite}`smith2010physical`, and [_Spectral Audio Signal Processing_](https://ccrma.stanford.edu/~jos/sasp/) {cite}`smith2011spectral`.
- **Audio programming and effects.** Richard Boulanger and Victor Lazzarini's _The Audio Programming Book_ {cite}`boulanger2010audio`, Will Pirkle's _Designing Audio Effect Plugins in C++_ {cite}`pirkle2019designing`, Udo Zölzer's _DAFX: Digital Audio Effects_ {cite}`zolzer2011dafx`, and Andy Farnell's _Designing Sound_ {cite}`farnell2010designing`, which designs sound effects from scratch in Pure Data.
- **Algorithmic composition.** Mary Simoni and Roger Dannenberg's _Algorithmic Composition: A Guide to Composing Music with Nyquist_ {cite}`simoni2013algorithmic`.
- **Music information retrieval.** Meinard Müller's _Fundamentals of Music Processing_ {cite}`muller2021fundamentals` and Alexander Lerch's _An Introduction to Audio Content Analysis_ {cite}`lerch2023introduction`.
- **Acoustics and mathematics.** Thomas Rossing, F. Richard Moore, and Paul Wheeler's _The Science of Sound_ {cite}`rossing2002science`, Neville Fletcher and Thomas Rossing's _The Physics of Musical Instruments_ {cite}`fletcher1998physics`, and Gareth Loy's _Musimathics_ {cite}`loy2006musimathics,loy2007musimathics`.
- **Perception and cognition.** Albert Bregman's _Auditory Scene Analysis_ {cite}`bregman1990auditory`.
- **History.** Thom Holmes's _Electronic and Experimental Music_ {cite}`holmes2020electronic`.
- **Online courses.** [_Audio Signal Processing for Music Applications_](https://www.coursera.org/learn/audio-signal-processing) by Xavier Serra and Julius O. Smith III on Coursera, and, on Kadenze, [_Introduction to Real-Time Audio Programming in ChucK_](https://www.kadenze.com/courses/introduction-to-real-time-audio-programming-in-chuck/info) and [_Programming Max: Structuring Interactive Software for Digital Arts_](https://www.kadenze.com/courses/programming-max-structuring-interactive-software-for-digital-arts/info).

### CMU courses

For readers who are CMU students, here are some courses that pick up where this book leaves off. The links point to the [CMU course catalog](https://coursecatalog.web.cmu.edu) or to the course websites.

- **Electronic music.** [57-421 Exploded Ensemble](https://coursecatalog.web.cmu.edu/search/?P=57-421), [57-344 Experimental Sound Synthesis](https://coursecatalog.web.cmu.edu/search/?P=57-344), [57-345 Twisted Signals: Multimedia Processing for the Arts](https://coursecatalog.web.cmu.edu/search/?P=57-345), and [57-347 Electronic and Computer Music](https://coursecatalog.web.cmu.edu/search/?P=57-347).
- **Recording and production.** [57-337 Sound Recording](https://coursecatalog.web.cmu.edu/search/?P=57-337), [57-338 Sound Editing and Mastering](https://coursecatalog.web.cmu.edu/search/?P=57-338), [57-438 Multitrack Recording](https://coursecatalog.web.cmu.edu/search/?P=57-438), and [57-562 Intro to Music Production with DAWs](https://coursecatalog.web.cmu.edu/search/?P=57-562).
- **Acoustics.** [33-114 Physics of Musical Sound](https://coursecatalog.web.cmu.edu/search/?P=33-114).
- **Signal processing.** [18-491/691 Digital Signal Processing](https://courses.ece.cmu.edu/18491) and [11-755 Machine Learning for Signal Processing](https://coursecatalog.web.cmu.edu/search/?P=11-755).
- **Interfaces.** [99-355 IDeATe: Introduction to Arduino](https://coursecatalog.web.cmu.edu/search/?P=99-355) and [24-104 TechSpark: Modern Making](https://coursecatalog.web.cmu.edu/search/?P=24-104).
- **Music AI.** [15-798 Generative AI for Music and Audio](https://gclef-cmu.org/15798-f25/) and [11-485/685/785 Introduction to Deep Learning](https://deeplearning.cs.cmu.edu).
- **Real-time systems.** 15-323 Computer Music Systems and Information Processing is no longer offered, but its [materials](https://www.cs.cmu.edu/~music/cmp/archives/cmsip/index.html) are archived online.
