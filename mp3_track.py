import mimetypes
import file_utils
import os
import re
from urllib.error import URLError
from urllib.request import urlopen
from mutagenx._id3util import ID3NoHeaderError
from mutagenx.id3 import ID3, COMM, TIT2, TPE1, TALB, TCON, TDRC, TRCK, TPE2, TCMP, APIC


class MP3Track:
    """An MP3 wrapper that allows for the reading and writing of its ID3 tag.

    Existing metadata is converted to ID3V2.4 upon saving.
    """

    # These are ID3V2.4 frame identifiers, NOT ID3V2.3!
    _KEY_TITLE = "TIT2"
    _KEY_ARTIST = "TPE1"
    _KEY_ALBUM_ARTIST = "TPE2"
    _KEY_ALBUM = "TALB"
    _KEY_GENRE = "TCON"
    _KEY_YEAR = "TDRC"
    _KEY_TRACK = "TRCK"
    _KEY_COMPILATION = "TCMP"
    _KEY_COMMENT = "COMM"
    _KEY_PICTURE = "APIC"

    def __init__(self, path):
        try:
            self._id3 = ID3(path)
        except ID3NoHeaderError:
            # If there is no ID3 tag already, just create one by saving a blank title tag.
            self._id3 = ID3()
            self._id3.add(TIT2())
            self._id3.save(path)
            # Reload the file to set the ID3 objects filename because saving to a path alone does not do that.
            self._id3.load(path)

        # This may be automatic, but ensure that all tags are ID3V2.4 just in case.
        self._id3.update_to_v24()

    def set_title(self, title):
        """Set the title.

        :param title: The title to set.
        :type title: str
        """

        self._id3.add(TIT2(encoding=3, text=title))

    def get_title(self):
        """Get the title.

        :returns: The title.
        :rtype: str
        """

        return self._get_frames_text(MP3Track._KEY_TITLE)

    def set_artist(self, artist):
        """Set the artist.

        :param artist: The artist to set.
        :type artist: str
        """

        self._id3.add(TPE1(encoding=3, text=artist))

    def get_artist(self):
        """Get the artist.

        :returns: The artist.
        :rtype: str
        """

        return self._get_frames_text(MP3Track._KEY_ARTIST)

    def set_album_artist(self, album_artist):
        """Set the album artist.

        :param album_artist: The album artist to set.
        :type album_artist: str
        """

        self._id3.add(TPE2(encoding=3, text=album_artist))

    def get_album_artist(self):
        """Get the album artist.

        :returns: The album artist.
        :rtype: str
        """

        return self._get_frames_text(MP3Track._KEY_ALBUM_ARTIST)

    def set_album(self, album):
        """Set the album.

        :param album: The album to set.
        :type album: str
        """

        self._id3.add(TALB(encoding=3, text=album))

    def get_album(self):
        """Get the album.

        :returns: The album.
        :rtype: str
        """

        return self._get_frames_text(MP3Track._KEY_ALBUM)

    def set_genre(self, genre):
        """Set the genre.

        :param genre: The genre to set.
        :type genre: str
        """

        self._id3.add(TCON(encoding=3, text=genre))

    def get_genre(self):
        """Get the genre.

        :returns: The genre.
        :rtype: str
        """

        return self._get_frames_text(MP3Track._KEY_GENRE)

    def set_year(self, year):
        """Set the year.

        :param year: The year to set.
        :type year: str

        :raise ValueError: Incorrect year format.
        """

        # Ensure that year is a 4 digit number. TDRC can take more complex dates, but limit it to just year for now.
        if re.match("^[0-9]{4}$", year):
            self._id3.add(TDRC(encoding=3, text=year))
        else:
            raise ValueError("Year must be of the form \"YYYY\".")

    def get_year(self):
        """Get the year.

        :returns: The year.
        :rtype: str
        """

        return self._get_frames_text(MP3Track._KEY_YEAR)

    def set_track(self, track):
        """ Set the track number and total track count.

        :param track: Track information of form "<track_number>", "<track_number>/<total_tracks>", or "/<total_tracks>."
        :type track: str

        :raise ValueError: Incorrect track format.
        """

        # Ensure that the track information is in the right format.
        if re.match("^[0-9]*/[0-9]*$", track):
            self._id3.add(TRCK(encoding=3, text=track))
        else:
            raise ValueError("Track must be of the form \"^[0-9]*/[0-9]*.\"")

    def get_track(self):
        """Get the track number and total track count.

        :returns: Track information of form "<track_number>", "<track_number>/<total_tracks>", or "/<total_tracks>."
        :rtype: str
        """

        return self._get_frames_text(MP3Track._KEY_TRACK)

    def set_part_of_compilation(self, is_part):
        """ Set whether or not this track is part of a compilation.

        :param is_part: True to set the track as part of a compilation, false otherwise.
        :type is_part: bool
        """

        if is_part:
            self._id3.add(TCMP(encoding=3, text="1"))
        else:
            self._id3.add(TCMP(encoding=3, text="0"))

    def get_part_of_compilation(self):
        """Get whether ot not this track is part of a compilation.

        :returns: True if the track is part of a compilation, false otherwise
        :rtype: bool
        """

        compilation_flag = self._get_frames_text(MP3Track._KEY_COMPILATION)
        if (compilation_flag is None) or (compilation_flag == '0'):
            return False
        else:
            return True

    def clear_comments(self):
        """Clear all comments."""

        # Clear all comment frames.
        self._delete_frames(MP3Track._KEY_COMMENT)

    # TODO: Research comment keys and figure out what the default value should be.
    def add_comment(self, comment, key="comment_key", clear_existing_comments=True):
        """ Add a comment.

        :param comment: A comment.
        :type comment: str

        :param key: A key for the comment so it can be accessed from the list of comments later. Defaults to "comment_key".
        :type key: str

        :param clear_existing_comments: True to clear all existing comments, false to keep them. Defaults to True.
        :type clear_existing_comments: bool
        """

        # There may already be a multiple comment frames. Delete them if it is requested.
        if clear_existing_comments:
            self.clear_comments()

        self._id3.add(COMM(encoding=3, lang="eng", desc=key, text=comment))

    def get_comments(self):
        """Get all comments.

        :returns: All comments.
        :rtype: str
        """

        return self._get_frames_text(MP3Track._KEY_COMMENT)

    def clear_pictures(self):
        """Clear all pictures."""

        # Clear all picture frames (no pun intended).
        self._delete_frames(MP3Track._KEY_PICTURE)

    def add_picture_from_file(self, path, clear_existing_pictures=True):
        """ Add a picture (more specifically an album cover) from a file.

        :param path: The path to the picture file to set as the picture.
        :type path: str

        :param clear_existing_pictures: True to clear all existing pictures, false to keep them. Defaults to True.
        :type clear_existing_pictures: bool

        :raise ValueError: Incompatible mime type.
        :raise IOError: Error opening file.
        """

        # There may already be a multiple picture frames. Delete them if it is requested.
        if clear_existing_pictures:
            self.clear_pictures()

        mime_type = mimetypes.guess_type(path)[0]
        if not mime_type in ["image/png", "image/jpeg"]:
            raise ValueError("Picture mime type must be either image/png or image/jpeg.")

        try:
            with open(path, "rb") as file:
                # A type of 3 refers to the album front cover.
                self._id3.add(APIC(encoding=3, mime=mime_type, type=3, desc="Front Cover", data=file.read()))
        except IOError:
            raise IOError("Unable to read file into tag: " + path)

    def add_picture_from_url(self, url, clear_existing_pictures=True):
        """ Add a picture (more specifically an album cover) from a URL.

        :param url: The url to the picture file to set as the picture.
        :type url: str

        :param clear_existing_pictures: True to clear all existing pictures, false to keep them. Defaults to True.
        :type clear_existing_pictures: bool

        :raise ValueError: Incompatible mime type.
        :raise URLError: Error opening URL.
        """

        # There may already be a multiple picture frames. Delete them if it is requested.
        if clear_existing_pictures:
            self.clear_pictures()

        mime_type = mimetypes.guess_type(url)[0]
        if not mime_type in ["image/png", "image/jpeg"]:
            raise ValueError("Picture mime type must be either image/png or image/jpeg.")

        try:
            with urlopen(url) as file:
                # A type of 3 refers to the album front cover.
                self._id3.add(APIC(encoding=3, mime=mime_type, type=3, desc="Front Cover", data=file.read()))
        except URLError:
            raise URLError("Unable to read url into tag: " + url)

    def clear_tag(self):
        """Clear all metadata from the ID3 tag.

        A save is still necessary for this change to persist.
        """

        # This removes the entire ID3 tag from file, it does NOT simply clear all values keeping the whole tag intact.
        self._id3.delete()

        # Add a blank title frame so a new ID3 tag is created and added to the file. Before calling save on the ID3
        # object, it will say that we have a TIT2 frame with no value. However, after calling save on the ID3 object and
        # reloading the file into a new ID3 object, this blank frame is apparently gone according to ID3.pprint() and
        # we are left with a cleared ID3 tag.
        self._id3.add(TIT2())

    def save_tag(self):
        """Save all changes to file."""
        self._id3.save()

    def get_file_path(self):
        """Get the file path for this track.

        :return: The file path for this track.
        :rtype: str
        """

        return self._id3.filename

    def rename_file(self, new_base_filename):
        """Renames this track's base filename.

        :param new_base_filename: The base filename to rename this track to. Does not include prefix path.
        :type new_base_filename: str

        :raise FileExistsError: File with the same name already exists.
        """

        original_path = self._id3.filename
        prefix_path = os.path.dirname(original_path)
        valid_filename = file_utils.ensure_valid_filename(new_base_filename)
        new_path = os.path.join(prefix_path, valid_filename)

        if os.path.exists(new_path):
            raise FileExistsError("Cannot rename file. File with same name already exists.")

        # Use replace in case support for other Windows and Linux is added. It is more portable than rename().
        os.replace(original_path, new_path)

        # Reload ID3 object so its filename attribute is up to date.
        self._id3.load(new_path)

    def _get_frames_text(self, identifier):
        """Get the text from all frames with a given frame identifier (frame type) as one string.

        :param identifier: The identifier of the type of frame text being requested.
        :type identifier: str

        :returns: A string that is made up of text from all frames with a given frame identifier (frame type). None if no such frames exist.
        :rtype: str or None
        """

        # Find all frames with the identifier.
        frames = self._get_frames(identifier)

        # Return early if there are no frames.
        if len(frames) == 0:
            return None

        # Concatenate all frames into one string.
        all_text = ""
        for frame in frames:
            for text in frame.text:
                # It is possible that a text entry is not a string (e.g. ID3TimeStamp)
                if type(text) != str:
                    all_text += text.get_text()
                else:
                    all_text += text

                all_text += " "

        # Remove the unnecessary last space.
        all_text = all_text.rstrip()

        return all_text

    def _get_frames(self, identifier):
        """Get all frames with a given frame identifier (frame type).

        :param identifier: The identifier of the type of frame being requested.
        :type identifier: str

        :returns: A list of all frames with a given frame identifier.
        :rtype: list
        """

        return self._id3.getall(identifier)

    def _delete_frames(self, identifier):
        """Delete all frames with a given frame identifier (frame type).

        :param identifier: The identifier of the type of frames to be deleted.
        :type identifier: str
        """

        self._id3.delall(identifier)

    def __str__(self):
        return self._id3.pprint()

if __name__ == "__main__":
    song = MP3Track("/Users/stephen/Downloads/song.mp3")

    print(song.get_title())
    print(song.get_artist())
    print(song.get_album_artist())
    print(song.get_album())
    print(song.get_genre())
    print(song.get_year())
    print(song.get_track())
    print(song.get_part_of_compilation())
    print(song.get_comments())

    song.set_title("TITLE")
    song.set_artist("ARTIST")
    song.set_album_artist("ALBUM ARTIST")
    song.set_album("ALBUM")
    song.set_genre("1")
    song.set_year("2121")
    song.set_track("1/99")
    song.set_part_of_compilation(False)
    song.add_comment("1", "COMMENT")
    song.add_comment("2", "ANOTHER COMMENT")
    song.add_picture_from_file("/Users/stephen/Downloads/cover.jpg")
    song.clear_tag()
    song.save_tag()

    print("\n")
    print(song.get_title())
    print(song.get_artist())
    print(song.get_album_artist())
    print(song.get_album())
    print(song.get_genre())
    print(song.get_year())
    print(song.get_track())
    print(song.get_part_of_compilation())
    print(song.get_comments())
