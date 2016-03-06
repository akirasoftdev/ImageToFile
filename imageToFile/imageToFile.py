from PIL import Image
import argparse
import math
import uuid

UUID_SIZE = 16
MAX_FILE_NAME_SIZE = 128
SEQUENTIAL_NUMBER_SIZE = 1
FILE_SIZE_SIZE = 8
HEADER_SIZE = 1
NAMELEN_SIZE = 1
BYTE_PER_PIXEL = 4

class Header:
    def __init__(self):
        self.uuid = ''
        self.seqnum = 1
        self.lastseqnum = 0
        self.filesize = 0
        self.bodysize = 0
        self.headersize = 0
        self.filename = b''

    def get_size(self):
        temp = UUID_SIZE + SEQUENTIAL_NUMBER_SIZE * 2 + \
            (FILE_SIZE_SIZE * 2) + HEADER_SIZE + NAMELEN_SIZE + len(self.filename)
        padding = (BYTE_PER_PIXEL - (temp % BYTE_PER_PIXEL) % BYTE_PER_PIXEL)
        return temp + padding


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

        bodysize_as_array = bytearray()
        for i in range(offset, offset + FILE_SIZE_SIZE):
            bodysize_as_array += get_bytes_from_image(data, i)
        header.bodysize = int.from_bytes(bodysize_as_array, 'little')
        offset += FILE_SIZE_SIZE

        header.headersize = int.from_bytes(get_bytes_from_image(data, offset), 'little')
        offset += HEADER_SIZE

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
    ret = bytes(data[num_of_pixel])[index_of_color:index_of_color+1]
    return ret

def transport_data(header, image, output_file, remaining_size):
    header_size = header.get_size()
    offset_as_pixel = int(header_size / BYTE_PER_PIXEL)
    offset_as_byte = header_size % BYTE_PER_PIXEL

    transport_size = header.bodysize

    start_index = int(header_size / BYTE_PER_PIXEL)
    end_index = math.ceil((header_size + transport_size) / BYTE_PER_PIXEL)
    for i in range(start_index, end_index):
        start_pos = 0
        end_pos = 4
        if i == start_index:
            start_pos = offset_as_byte
        elif i == (end_index - 1):
            end_pos = transport_size % BYTE_PER_PIXEL
            if (end_pos == 0):
                end_pos = BYTE_PER_PIXEL
            print("end_pos = %d" % end_pos)
            if (end_pos != 4):
            	print("break")
        output_file.write(bytes(image.getdata()[i][start_pos:end_pos]))
    return transport_size

def get_filename(uuid, seqnum):
    return uuid.hex + '_' + str(seqnum) + '.png'

def get_filepath(path):
    if (path.rfind('\\') == -1):
        return ''
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
    uuid = header.uuid
    path = get_filepath(args.in_file_path)
    filename = get_filename(uuid, header.seqnum)
    output_file = open(header.filename.decode(), 'wb')
    remaining_size = header.filesize
    lastseqnum = header.lastseqnum

    for i in range(1, lastseqnum + 1):
        header.seqnum = i
        if (len(path) == 0):
            full_path = get_filename(uuid, i)
        else:
            full_path = path + '\\' + get_filename(uuid, i)
        header = load_fileheader(full_path)
        input_file = open(full_path, 'rb')
        image = Image.open(input_file)
        wrote_size = transport_data(header, image, output_file, remaining_size)
        remaining_size -= wrote_size
        input_file.close()
    output_file.close()

if __name__ == '__main__':
    main()
