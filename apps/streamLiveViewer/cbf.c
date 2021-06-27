#include <string.h>
#include <stdio.h>
#include <stdint.h>

typedef union 
{
    const char* cp;
    const uint8_t* uint8;
    const uint16_t* uint16;
    const int16_t* int16;
    const int32_t* int32;
} EncodedValue;

// decode CBF BYTE OFFSET compression algorithm
void decode(const char* input, int blob_size, int32_t* output)
{
    int32_t diff;
    int32_t val = 0;
    EncodedValue enc;
    enc.cp = input;
    while ((enc.cp - input) < blob_size) {
        if (*enc.uint8 != 0x80) {
            diff = (int)*enc.cp++;
        }
        else {
            enc.cp++;
            if (*enc.uint16 != 0x8000) {
                diff = (int)*enc.int16++;
            }
            else {
                enc.uint16++;
                diff = *enc.int32++;
            }
        }
        val += diff;
        *output = val;
        output++;;
    }
}

void read_cbf(char* cbf, int32_t* output, double* exposure_time)
{
    char* ptr = strstr(cbf, "X-Binary-Size:");
    if (!ptr) {
        printf("Bad header - cannot find X-Binary-Size\n");
    }
    ptr += strlen("X-Binary-Size:");
    int blob_size;
    if (sscanf(ptr, "%d", &blob_size) != 1) {
        printf("Error getting binary size\n");
        return;
    }
    
    ptr = strstr(cbf, "Exposure_time");
    ptr += strlen("Exposure_time");
    if (sscanf(ptr, "%lf", exposure_time) != 1) {
        printf("Error getting exposure time\n");
        return;
    }
    
    const char* header_end_mark = "\x0C\x1A\x04\xD5";
    ptr = strstr(cbf, header_end_mark);
    if (!ptr) {
        printf("Coudn't find end of header mark in file\n");
        return;
    }
    const char* blob = ptr + strlen(header_end_mark);
    decode(blob, blob_size, output);
}
