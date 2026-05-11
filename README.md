Introducing! badadabuM!


# NullSuite!


....yeah I know.

I used to have all these programs on here as separate gits, but since 99% of the filesize was the virtual environment?

I decided to combine them, and throw them into a launcher of sorts. (all my git history 😭 it's all GONE... oh well.)

And since now, due to that monstrosity, I said fuck it and now have it check/auto update with git if you set it up right.

ANYWAYS if you didn't see the old gits, or haven't been following. Let's get into it.


---

NullSuite is a combination of all the NullForgeStudio tools I use on Linux (Mint specifically, other distros maybe coming after/if this takes off).

There was a problem > I coded a way to fix it.  
Simple as.

Usually I made Python and Bash scripts to just run in the background and do nothing, but people like UI.

So I used the simplest lightweight UI I could. Tkinter!

YEAH! That UI software that looks like Windows 95 from 1991? Love that shit! Simple. Sleek. Functional. Fast.

So will these programs look nice? NOT A CHANCE. Will they perform? Sure will... at least when I work out the kinks.

I tried to make this as simple as possible, you know, for all those people moving from Windows to Linux (proud of you btw!)

SO. here's how it goes.

---

# Installation

You have 2 options.

1. Cloning the Repo

> Find a folder you like. Open a terminal. Paste this:

> `git clone https://github.com/NullForgeStudiosVex/NullSuite.git`

> Hit enter, and bam, you have it downloaded.

2. Downloading the .zip.

> Up top there. If you don't know how git works (neither do I most of the time, let's not lie.)

> You'll see a green `< > Code` button. Click that, then Download ZIP.

> Unzip into a folder you like.


Once you got this hot piece of garbage downloaded.

Open the folder it's in. Open a terminal.

Copy this:

`chmod +x InstallNullSuite(Mint).sh`

Then double click InstallNullSuite(Mint).sh

And it will pretty much do everything you need it to do.

HOWEVER, if you did the 2nd install option of grabbing the .zip

It will ask you if you want automatic updates. If you say yes... it asks for a location, and clones the repo there, and deletes the .zip folder you just downloaded. fuckin lol.

If not, well that's on you. Doesn't matter.

Anyways ONTO what these things even ARE that you're downloading?

---

FIRST THINGS FIRST (that's a dumb phrase)

Yeah I could merge all this into an AppImage, or a flatpak, or any of that other dumb shit. I absolutely *could*

But you know what?

When the apps in here are like, asking to take control of your mouse, and your audio?

I think I'd rather let my shitty source code show that... this is doing NOTHING nefarious. Code can't be trusted these days anymore. Not even Micro$lops 😒

*ahem*

You WILL require X11 for these programs to work.

If you're on Wayland... well... kind of on your own there. Too restrictive at the moment.

Anyways onto the programs...



# NullWire!


> Requires: X11, PipeWire, Python 3, Tkinter


NullWire is a mock-up of Virtual Audio Cable... for Linux!

Because of that it requires, and is built around PipeWire.

Thankfully most distros use PipeWire natively so that's good.

BUT basically what this program does is:

You attach your output, and input devices to it.

You then create sinks (wires).

You then toggle which device you want to go to that wire (only devices that were set up can be attached)

You then attach the audio source you want to the wire.


So say you create a wire, and you have Spotify playing.

You click Add Source, click Spotify on that wire, and now Spotify only plays on that wire.

Where you can hear Spotify playing depends on what audio device you attached to the wire. Easy.



It "controls" your audio in a sense. So yeah. 


I use this a lot for streaming to OBS so I can control audio sources better 😃

---

# NullCursor!


> Requires: X11, PipeWire, xrandr, xdotool, Python 3, Tkinter


Windows has innate multi-monitor support anymore.

Linux... kind of doesn't.

The workaround? NullCursor.



In short, my buddy has a 4k monitor, and a 1080 monitor. They don't line up.

Trying to go from the 4k monitor to the 1080 monitor just makes you bump the side.

NullCursor lets you select monitor 1. Then monitor 2. Select your teleportation angle (4k monitor top right) to (1080p monitor top left)

And when your mouse cursor hits the top right of the 4k monitor, it "teleports" to the 1080's top left corner.

YOU CAN set the parameters of warping e.g. how close the mouse has to be to the corner, when the system starts scanning so it just idles in the back when the mouse isn't near the corner. Stuff like that.



But it DOES "control" your mouse. In the way of forcefully moving it to the coordinates of the other monitor.

So 🤷

It also lets you have monitor "setups" e.g. profiles.

Sometimes I have monitor 1,2,3 turned on at my desk.

But when I'm doing other things, I have monitor 2,3,4 turned on.


By simply clicking on the "Activate profile" button on the list... bam. Monitors switch what's on. In an instant. FPS and locations and everything saved.

When you create a profile it creates a copy of exactly how it is. Primary monitor. FPS rates. Locations. All that. 😃 no messy configs needed.


I use that a lot when switching from my work desk to my drum setup. Very nifty.

---

# NullMidi!


> Requires: X11, mido, python-rtmidi, python-uinput, Python 3, Tkinter



This was kinda created for a silly reason but.

Did you know Proton can't take in MIDI data?

Or when it can it's very complicated to set up? Annoying, but this was my fix.


Wanted to play Clone Hero with the wife. Can't. Drums aren't recognized cause no MIDI.

So I made this little program that intakes MIDI signals (from specified device) and then simulates a keypress when touched/used/whatever.


Hit the drum pad? The letter K is produced.

I also used it for my Stream Deck. Hit a button on it, it sends CTRL+SHIFT+K to my comp. Things happen.


Ya just click add.

Set the dropdown to the MIDI device you want.

Hit the MIDI key

Set the keyboard input you want.

¯\_(ツ)_/¯ don't have to touch a damn thing.


Speaking of Proton...

---

# NullProton!


> Requires: X11, Proton, Python 3, Tkinter



Sometimes you don't want to have to add a temporary game to your Steam library as a non-Steam product just to run Proton... I know I don't.

With this handy tool, you set your preferred Proton (I prefer GE) — plan to add more support for multiple Proton versions in the future, just can't be fucked atm —

Click "add game"

Then browse to the .exe, click launch, and there ya go ¯\_(ツ)_/¯ games launching through Proton.


OH quick thing (lol). When going through InstallNullSuite, you can set up your default Proton preemptively.

Doing so will create a .desktop

And then without having to open NullProton you can have a quick launcher. Just right click an exe and "Open with NullProton" will show up.


NOW because it's a quick launcher like this, it isn't as strong as natively running it through NullSuite.

So if you experience any issues, run it through NullSuite.

And if you have any issues after THAT... either the game doesn't run, or add it as a non-Steam game on Steam.

A faked environment is strong as hell, but sometimes faking it doesn't work.


---

# NullRip!

> Requires: handbrake-cli, python3-tk
> Optional: vlc

(bout time I made this.)

NullRip is a lightweight DVD/BluRay ripping frontend for HandBrakeCLI.

Because honestly?
Using HandBrakeCLI raw in terminal works fine... until you forget half the damn arguments 3 months later.

So this fixes that.

Features:
- Disc scanning
- Title/chapter selection
- Audio/subtitle selection
- Chapter previewing through VLC
- Automatic MKV output
- Progress + ETA overlay
- Cancel ripping mid-process
- Open output folder after completion

Workflow is simple:

1. Insert disc
2. Browse to the mounted media
3. Hit Scan
4. Pick your title/chapters/audio/subtitles
5. Name the file
6. Hit Start

Done.

No weird presets.
No giant bloated UI.
No Electron.
No telemetry.
No cloud bullshit.

Just:
DVD in.
Video out.

Previewing chapters requires VLC.
If VLC isn't installed? The preview button just won't work. That's it. Get VLC ya chud.

NullRip is mainly designed around DVDs currently.
BluRay support may happen later if I can be fucked dealing with the nightmare that is BluRay DRM, and spend 200$+ on a bluray drive 😒


---
# Ending Thoughts

That's all for now until I add more programs to this thing.

Like mentioned before, I had all these as just scripts laying around. Decided to merge them together and give them a simple UI for people. ¯\_(ツ)_/¯ so yeah.

Enjoy.


If there are any questions/suggestions/bugs? Join the NFS Discord. Because I'll be honest.

I can't be fucked managing 500 places to reach me and other websites. Got shit to do, not be on social media.

And if you ever feel inclined, here is our Ko-fi so you can make donations, so I have more money to make things better.

(Some things I want to make require hardware... that's pricey so ¯\_(ツ)_/¯)


## [Discord](https://discord.gg/NgFTdR3fZJ)

## [Ko-fi](https://ko-fi.com/nullforgestudios)


Don't like Discord/Ko-fi? Welp... don't know what to tell ya.


Toodles!

I never say that.