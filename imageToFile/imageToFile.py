from PIL import Image
import argparse
import math
import uuid

UUID_SIZE = 16
MAX_FILE_NAME_SIZE = 128
SEQUENTIAL_NUMBER_SIZE = 1
FILE_SIZE_SIZE = 8
NAMELEN_SIZE = 1
BYTE_PER_PIXEL = 4

class Header:
    def __init__(self):
        self.filename = b''
        self.uuid = ''
        self.seqnum = 1
        self.lastseqnum = 0
        self.filesize = 0

    def get_size(self):
        return UUID_SIZE + SEQUENTIAL_NUMBER_SIZE * 2 + len(self.filename) + NAMELEN_SIZE + FILE_SIZE_SIZE

    def from_bytes(data):
        header = Header()
        uuid_as_array = bytearray()
        offset = 0
        for i in range(offset, UUID_SIZE):
            uuid_as_array += get_bytes_from_image(data, i)
        header.uuid = uuid.UUID(bytes=bytes(uuid_as_array))
        offset += UUID_SIZE

        header.seqnum = int.from_bytes(get_bytes_from_image(data, offset), 'little')
        offset += SEQUENTIAL_NUMBER_SIZE

        header.lastseqnum = int.from_bytes(get_bytes_from_image(data, offset), 'little')
        offset += SEQUENTIAL_NUMBER_SIZE

        filesize_as_array = bytearray()
        for i in range(offset, offset + FILE_SIZE_SIZE):
            filesize_as_array += get_bytes_from_image(data, i)
        header.filesize = int.from_bytes(filesize_as_array, 'little')
        offset += FILE_SIZE_SIZE

        namelen = get_bytes_from_image(data, offset)
        offset += NAMELEN_SIZE

        filename_as_array = bytearray()
        for i in range(offset, offset + int.from_bytes(namelen, 'little')):
            filename_as_array += get_bytes_from_image(data, i)
        header.filename = filename_as_array
        return header

def get_bytes_from_image(data, index):
    num_of_pixel = math.floor(index / BYTE_PER_PIXEL)
    index_of_color = index % BYTE_PER_PIXEL
    return data[num_of_pixel][index_of_color].to_bytes(1, 'little')

def transport_data(header, image, output_file, remaining_size):
    outbuff = bytearray()
    offset = header.get_size()
    for i in range(0, image.width * image.height * BYTE_PER_PIXEL - offset):
        outbuff += get_bytes_from_image(image.getdata(), offset + i)

    write_size = len(outbuff)
    if (write_size > remaining_size):
        write_size = remaining_size
    output_file.write(outbuff[:write_size])
    return write_size

def get_filename(header):
    return header.uuid.hex + '_' + str(header.seqnum) + '.png'

def get_filepath(path):
    return path[:path.rfind('\\')]

def load_fileheader(file_path):
    input_file = open(file_path, 'rb')
    image = Image.open(input_file)
    header = Header.from_bytes(image.getdata())
    input_file.close()
    return header

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('in_file_path', action='store', type=str, help='File Path')
    args = parser.parse_args()

    header = load_fileheader(args.in_file_path)
    path = get_filepath(args.in_file_path)
    filename = get_filename(header)
    output_file = open(header.filename.decode(), 'wb')
    remaining_size = header.filesize

    for i in range(header.seqnum, header.lastseqnum + 1):
        header.seqnum = i
        full_path = path + '\\' + get_filename(header)
        input_file = open(full_path, 'rb')
        image = Image.open(input_file)
        wrote_size = transport_data(header, image, output_file, remaining_size)
        remaining_size -= wrote_size
        input_file.close()
    output_file.close()

if __name__ == '__main__':
    main()
