// fpraw: Chromaprint fingerprint of raw signed 16-bit little-endian PCM read from stdin.
#include <chromaprint.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
int main(int argc, char **argv) {
    int rate = 11025, channels = 1, maxSeconds = 120;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "-r") && i + 1 < argc) rate = atoi(argv[++i]);
        else if (!strcmp(argv[i], "-c") && i + 1 < argc) channels = atoi(argv[++i]);
        else if (!strcmp(argv[i], "-l") && i + 1 < argc) maxSeconds = atoi(argv[++i]);
        else if (!strcmp(argv[i], "-v")) { printf("%s\n", chromaprint_get_version()); return 0; }
    }
    ChromaprintContext *ctx = chromaprint_new(CHROMAPRINT_ALGORITHM_DEFAULT);
    if (!chromaprint_start(ctx, rate, channels)) return 2;
    const size_t maxSamples = (size_t)maxSeconds * rate * channels;
    size_t total = 0;
    std::vector<int16_t> buf(16384);
    while (total < maxSamples) {
        size_t want = buf.size();
        if (want > maxSamples - total) want = maxSamples - total;
        size_t n = fread(buf.data(), sizeof(int16_t), want, stdin);
        if (n == 0) break;
        if (!chromaprint_feed(ctx, buf.data(), (int)n)) return 3;
        total += n;
    }
    if (!chromaprint_finish(ctx)) return 4;
    char *fp = NULL;
    if (!chromaprint_get_fingerprint(ctx, &fp)) return 5;
    printf("DURATION=%d\nFINGERPRINT=%s\n", (int)(total / channels / rate), fp);
    chromaprint_dealloc(fp);
    chromaprint_free(ctx);
    return 0;
}
