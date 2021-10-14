import copy
import os
import mido


DATA_FOLDER = "./midi/"
OUTPUT_FOLDER = "./output/"
FILTERED_PROGRAM_NUM = list(range(8, 16)) + list(range(112, 128))
FILTERED_CHANNEL = 9
UNIQUE_NOTE_THRESHOLD = 3


def isValid(track): 
    """
    check if the current track is a valid vocal track
    filters: 
        1. no overlap
        2. have notes
        3. filter bass/drum program number
        4. filter channel=9
        5. filter unique note cnt <= threshold
    """
    unique_note = set()
    for idx in range(len(track)-1):
        curr_note = track[idx]

        # filter by program number 
        if curr_note.type == "program_change" and curr_note.program in FILTERED_PROGRAM_NUM:
            return False

        # filter by channel=9
        if curr_note.type == "note_on" and curr_note.channel == FILTERED_CHANNEL:
            return False

        next_note = track[idx+1]
        if curr_note.type == "note_on" and curr_note.velocity > 0:
            unique_note.add(curr_note.note)
            if next_note.type == "note_on" and next_note.velocity > 0:
                return False
    
    # filter by unique note cnt
    if len(unique_note) <= UNIQUE_NOTE_THRESHOLD:
        return False
    
    return True

def extractVocalTracks(path, file_name):
    """
    extract tracks[track_idx] as a separate midi file    
    """
    file_path = os.path.join(path, file_name)
    print("Processing file: ", file_path)

    old_midi = mido.MidiFile(file_path)

    # filter midi files that has multiple tracks
    tempo_cnt = 0
    for meta_msg in old_midi.tracks[0]:
        if hasattr(meta_msg, "tempo"):
            tempo_cnt += 1
    if tempo_cnt >= 2:
        print("Skipping: {} has {} tempos".format(file_name, tempo_cnt))
        return

    new_midi = copy.deepcopy(old_midi)
    
    # move tempo to tracks[0][0]
    for idx in range(len(new_midi.tracks[0])):
        if hasattr(meta_msg, "tempo"):
            new_midi.tracks[0][0], new_midi.tracks[0][idx] = \
                new_midi.tracks[0][idx], new_midi.tracks[0][0]
            break

    for track_idx in range(len(old_midi.tracks)):
        if isValid(old_midi.tracks[track_idx]):
            new_file_path = os.path.join(OUTPUT_FOLDER, file_name.split(".")[0]+str(track_idx)+".mid")
        
            new_midi.tracks = []
            new_midi.tracks.append(old_midi.tracks[0])
            new_midi.tracks.append(old_midi.tracks[track_idx])
            print("Saving track %d to new file: " % track_idx, new_file_path)
            new_midi.save(new_file_path)


def process():
    """
    loop over the midi data folder
    extract all the vocal tracks and save as separate output files
    """
    for path, _, file_list in os.walk(DATA_FOLDER):
        for file_name in file_list:
            print("******************")
            try:
                extractVocalTracks(path, file_name)     
            except Exception as e:
                print("ERROR info: ", repr(e))
                print("Skip file: ", file_name)


if __name__ == "__main__":
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    process()