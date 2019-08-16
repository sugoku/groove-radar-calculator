# Groove Radar Calculator for StepMania charts by BedrockSolid

from __future__ import print_function, division
from builtins import input
from io import open

import sys, mutagen, argparse, traceback, wave

gms = {
    "dance-single": [4,"dancesingle"],
    "pump-single": [5,"pumpsingle"],
    "pump-single-p": [5,"pumpsingle"],
    "solo": [6,"solo"],
    "dance-double": [8,"dancedouble"], 
    "technomotion": [9,"technomotion"],
    "pump-halfdouble": [10,"pumpdouble"],
    "pump-double": [10,"pumpdouble"],
    "pump-double-p": [10,"pumpdouble"],
    "pump-couple": [10,"pumpdouble"],
    "pump-routine": [10,"pumpdouble"],
}

def get_notes(fn, sim):
    note = [[['','0'],[],[0,0]]] # [[[mode, difficulty], [notes], [start line, last line]], ]
    tempgm = ""
    if fn.split('.')[1] == 'ssc':
        for i in range(len(sim)):
            note[-1][2][0] = i
            if "#STEPSTYPE:" in sim[i]:
                tempgm = sim[i].replace("#STEPSTYPE:", "").replace(";", "").replace('\n', '').replace('\r', '')
                note[-1][0][0] = tempgm
            elif "#METER:" in sim[i]:
                note[-1][0][1] = sim[i].replace("#METER:", "").replace(";", "").replace('\n', '').replace('\r', '')
            elif "#NOTES:" in sim[i]:
                notestr = ""
                for a in range(i + 1, len(sim)):
                    if "//" not in sim[a]:
                        tempstr = sim[a].replace('\n', '').replace('\r', '').split('//')[0]
                        if ';' in tempstr:
                            notestr += tempstr.replace(';', '')
                            note[-1][2][1] = a
                            break
                        notestr += tempstr
                noteslist = notestr.split(",")
                for b in range(len(noteslist)):
                    n = get_gm_num(tempgm)
                    note[-1][1].append([noteslist[b][i:i+n] for i in range(0, len(noteslist[b]), n)]) # splits every n arrows into separate strings
                note.append([['','0'],[],[0,0]])
                i = a
    elif fn.split('.')[1] == 'sm':
        for i in range(len(sim)):
            note[-1][2][0] = i
            if "#NOTES:" in sim[i]:
                notestr = ""
                i += 1
                while ':' not in sim[i+1]:
                    i += 1
                for j in range(5):
                    if ':' in sim[i+1]:
                        if j == 0:
                            note[-1][0][0] = sim[i].strip().replace(":", "").replace('\n', '').replace('\r', '')
                            tempgm = note[-1][0][0]
                        elif j == 3:
                            note[-1][0][1] = sim[i].strip().replace(":", "").replace('\n', '').replace('\r', '')
                    i += 1
                for a in range(i + 1, len(sim)):
                    if "//" not in sim[a]:
                        tempstr = sim[a].replace('\n', '').replace('\r', '').split('//')[0]
                        if ';' in tempstr:
                            notestr += tempstr.replace(';', '')
                            note[-1][2][1] = a
                            break
                        notestr += tempstr
                noteslist = notestr.split(",")
                for b in range(len(noteslist)):
                    n = get_gm_num(tempgm)
                    note[-1][1].append([noteslist[b][i:i+n] for i in range(0, len(noteslist[b]), n)]) # splits every n arrows into separate strings
                note.append([['','0'],[],[0,0]])
                i = a
    return note[:-1]
    
def get_bpms(sim):
    #print(sim)
    for i in range(len(sim)):
        if "#BPMS:" in sim[i]:
            b = ""
            while ';' not in sim[i]:
                b += sim[i].replace("#BPMS:", '').replace(';', '').replace('\n', '').replace('\r', '')
            b += sim[i].replace("#BPMS:", '').replace(';', '').replace('\n', '').replace('\r', '')
            bpms = b.split(',')
            for i in range(len(bpms)):
                bpms[i] = bpms[i].split('=')     
            return bpms
    return []

def get_stops(sim):
    for i in range(len(sim)):
        if "#STOPS:" in sim[i]:
            s = ""
            while ';' not in sim[i]:
                s += sim[i].replace("#STOPS:", '').replace(';', '').replace('\n', '').replace('\r', '')
            s += sim[i].replace("#STOPS:", '').replace(';', '').replace('\n', '').replace('\r', '')
            stops = s.split(',')
            for i in range(len(stops)):
                stops[i] = stops[i].split('=')     
            return stops
    return []

def get_gm_num(gm): # how many arrows per gamemode
    try:
        return gms[gm][0]
    except:
        print(traceback.format_exc())
        print("Could not determine gamemode, defaulting to 4 arrows")
        return 4

def songlength(song):
    try:
        return song.info.length
    except:
        return song.getnframes() / song.getframerate()
    
def sum1and2(arr):
    summed = 0
    valid = ['1','2','4','X','x','Y','y','S','v']
    for beat in arr:
        for note in beat:
            summed += int(sum([note.count(x) for x in valid]) >= 1) # to include jumps as two notes add the counts directly
    return summed
    
def notetofract(arr): # RED=0, BLUE=2, YELLOW=4, GREEN=5 
    # create a list of notes like (color int, distance from last note in beats)
    # this includes 1, 2, 4, and M
    valid = ['1','2','4','M','X','x','Y','y','S','v']
    fract = []
    last = 0
    for beat in range(len(arr)):
        for note in range(len(arr[beat])):
            if any(x in arr[beat][note] for x in valid):
                color = 5
                fraction = note / len(arr[beat])
                if fraction % 0.25 == 0:
                    color = 0
                elif fraction % 0.125 == 0:
                    color = 2
                elif fraction % 0.0625 == 0:
                    color = 4
                current = beat+fraction
                fract.append([color, current - last])
                last = current
    return fract

def sumjumps(arr): # any with 1/2 at same time
    summed = 0
    valid = ['1','2','4','X','x','Y','y','S','v']
    for beat in arr:
        for note in beat:
            if sum([note.count(x) for x in valid]) >= 2:
                summed += 1
    return summed
    
def summines(arr): # just M
    sum = 0
    for beat in arr:
        for note in beat:
            sum += int(note.count('M') >= 1)
    return sum
    
def sumfreezetime(arr): # measure time between 2 and 3 in same lanes and add up fraction based on array length
    gm_num = len(arr[0][0])
    last = [-1 for i in range(gm_num)]
    sum = 0
    for beat in range(len(arr)):
        for note in range(len(arr[beat])):
            for i in range(gm_num):
                if arr[beat][note][i] == '2' or arr[beat][note][i] == '4':
                    last[i] = beat + (note / len(arr[beat]))
                elif arr[beat][note][i] == '3':
                    if last[i] == -1:
                        sys.exit("This simfile does not have correct holds and thus is broken. Aborting...")
                    sum += beat + (note / len(arr[beat])) - last[i]
                    last[i] = -1
    return sum
   
def getbpmchanges(bpm, stop): # check beat order and just make a list of bpms in order with stops inserted as 0
    stop = [[float(s[0]), 0] for s in stop]
    bpm = [[float(b[0]), float(b[1])] for b in bpm]
    all = bpm + stop
    all.sort(key=lambda x: x[0])
    i = 0
    while i < len(all)-1:
        if all[i][0] == all[i+1][0] and all[i+1][1] == 0:
            del all[i]
        else:
            i += 1
    #print(all)
    return [a[1] for a in all]
    
def gr_stream(note, song):
    sum = sum1and2(note)
    npm = (60 * sum) // songlength(song)
    return (npm - 139) * 100 / 161 if npm > 300 else npm / 3
    
def gr_voltage(note, song):
    avgbpm = 60 * len(note) / songlength(song)
    i = 0
    maxdensity = 0
    for i in range(len(note) - 4):
        temp = sum1and2(note[i:i+4])
        if temp > maxdensity:
            maxdensity = temp
    if i == 0:
        maxdensity = sum1and2(note)
    maxnpm = avgbpm * maxdensity // 4
    return (maxnpm + 330) * 10 / 93 if maxnpm > 600 else maxnpm / 6

def gr_air(note, song):
    jpm = 60*(sumjumps(note)+summines(note))//songlength(song)
    return (jpm + 5) * 5 / 3 if jpm > 55 else jpm * 20 / 11
    
def gr_freeze(note):
    freezelen = sumfreezetime(note)
    #print("Total freeze length: %s" % freezelen)
    farrowrate = 10000 * freezelen // len(note)
    return (farrowrate + 2484) * 100 / 5984 if farrowrate > 3500 else farrowrate / 35
    
def gr_chaos(note, song, bpms, stops):
    sum = sum1and2(note)
    fract = notetofract(note)
    # abnormality = sum*color/distance
    basechaos = 0
    for f in fract:
        basechaos += sum * f[0] / f[1] # abnormality
    bpmchanges = getbpmchanges(bpms, stops)
    #print(bpmchanges)
    totalbpmchange = 0
    i = 0
    lastnonzero = bpmchanges[0]
    while i < len(bpmchanges):
        if bpmchanges[i] != 0:
            lastnonzero = bpmchanges[i]
            if i+1 < len(bpmchanges):
                totalbpmchange += abs(bpmchanges[i] - bpmchanges[i + 1])
            else:
                totalbpmchange += bpmchanges[i]
        elif i+1 < len(bpmchanges):
            totalbpmchange += bpmchanges[i + 1] if bpmchanges[i + 1] > 0 else lastnonzero
        else:
            totalbpmchange += lastnonzero
        i += 1
    bpmchangepm = 60 * totalbpmchange / songlength(song)
    chaosdegree = basechaos * (1 + (bpmchangepm / 1500))
    chaosunit = chaosdegree * 100 / songlength(song)
    return (chaosunit + 21605) * 100 / 23605 if chaosunit > 2000 else chaosunit / 20
    
def main():
    parser = argparse.ArgumentParser(description='Calculate groove radar for StepMania charts.')
    parser.add_argument('fn')
    parser.add_argument('audfn')
    args = parser.parse_args()
    
    if args.fn == None:
        sys.exit("You did not input a StepMania simfile filename!")
    if args.audfn == None:
        sys.exit("You did not input an audio filename!")
        
    audext = args.audfn.split('.')[1]
    if audext == 'wav':
        song = wave.open(args.audfn, 'r')
    else: 
        song = mutagen.File(args.audfn)
    
    with open(args.fn, 'r') as f:
        lines = f.readlines()
        notes = get_notes(args.fn, lines)
        if args.fn.split('.')[1] == 'sm':
            bpms = get_bpms(lines)
            stops = get_stops(lines)
        for note in notes:
            #print(note[2])
            #print(len(lines))
            if args.fn.split('.')[1] == 'ssc':
                bpms = get_bpms(lines[note[2][0]:note[2][1]+1])
                stops = get_stops(lines[note[2][0]:note[2][1]+1])
            print(note[0])
            print("Stream: %s" % gr_stream(note[1], song))
            print("Voltage: %s" % gr_voltage(note[1], song))
            print("Air: %s" % gr_air(note[1], song))
            print("Freeze: %s" % gr_freeze(note[1]))
            print("Chaos: %s" % gr_chaos(note[1], song, bpms, stops))
            print()

if __name__ == '__main__':
    main()