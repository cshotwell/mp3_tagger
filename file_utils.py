import glob
import os


def get_mp3_files(path):
    """Finds all music files in a directory non-recursively.

    :param path: The path in which to look for music files.
    :type path: str

    :returns: A list of all music files that were found.
    :rtype: list
    """

    # TODO: Account for bug in glob module in Python versions < 3.4.
    # - Before Python 3.4, the glob module didn't automatically escape metacharacters. Escape ?, *, [, and ]. Simply
    #   replace with [?], [*], [[], []]. When using regex to make a substitution/replacement, make sure not to replace
    #   the brackets added by the prior substitutions with escaped brackets. That would result in "double escaped"
    #   brackets.

    return glob.glob(glob.escape(path) + "/*.mp3")


def ensure_valid_filename(filename):
    """Ensures a valid filename by removing any invalid characters and capping the length to 255.

    This method should be used on base filenames only and not entire paths.

    :param filename: A potentially invalid filename
    :type filename: str

    :returns: A valid filename.
    :rtype: str
    """

    # TODO: If I ever support Windows...
    # - Use the following method to remove any invalid characters from the base filenames:
    #   Create a dictionary a that maps each character that is not allowed in a valid filename to None. This dictionary
    #   can be passed into str.translate(table) for Unicode strings in order to remove the invalid characters. If we
    #   were not working with unicode strings below, str.translate(None, "\/:*?"<>|") would be much cleaner. The
    #   translate() method behaves differently depending on string type and is very confusing.
    #   windows_invalid_characters_map = {ord(char): None for char in '<>:"/\|?*'}
    # - I think the ENTIRE path for a file can only be 260 characters in Windows in most cases compared to OS X where
    #   each component can be 255 characters alone. I could be completely wrong on this though.

    # Separate off the extension from the root filename.
    (root, extension) = os.path.splitext(filename)

    # Remove the only invalid character that OS X does not support, ':'. Also limit the length of the root filename so
    # that the length of the resulting string plus the extension do not exceed 255 characters.
    root = root.replace(':', '')[0:(255 - len(extension))]

    return root + extension

if __name__ == "__main__":
    # The following filename is 255 characters plus some random colons and a ".txt" extension.
    print(ensure_valid_filename("::::Lorem ipsum dolor si::::::t amet, nonummy ligula volu::::tpat hac integer nonummy."
                                " Suspendisse ultricies, congue etiam tellus, erat libero, nulla eleifend, mauris pelle"
                                "ntesque. Suspendisse integer praesent vel, integer gravida mauris, fringilla vehicula "
                                "lacinia non.txt"))

    # Print a list of music files in my music directory.
    print(get_mp3_files("/Users/stephen/Music"))
