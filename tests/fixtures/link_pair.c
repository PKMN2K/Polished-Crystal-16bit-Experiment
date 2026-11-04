/* SameBoy cable adapter. Game state is observed, never injected.
 * The serial callbacks mirror SameBoy's libretro dual-device implementation.
 * Each CPU runs at most one instruction ahead of its peer. */
#include "gb.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

typedef struct Pair Pair;
typedef struct {
    Pair *pair;
    GB_gameboy_t *gb;
    unsigned index;
    bool outgoing;
    uint64_t cycles, bits, collisions;
    uint32_t pixels[160 * 144];
} Peer;
struct Pair { Peer peers[2]; uint64_t target; };

static uint32_t rgb(GB_gameboy_t *gb, uint8_t r, uint8_t g, uint8_t b)
{
    (void)gb;
    return r | (g << 8) | (b << 16) | 0xff000000u;
}
static void serial_start(GB_gameboy_t *gb, bool bit)
{
    Peer *p = GB_get_user_data(gb);
    p->outgoing = bit;
}
static bool serial_end(GB_gameboy_t *gb)
{
    Peer *p = GB_get_user_data(gb), *other = &p->pair->peers[p->index ^ 1];
    bool bit = GB_serial_get_data_bit(other->gb);
    GB_serial_set_data_bit(other->gb, p->outgoing);
    p->bits++;
    return bit;
}
static void log_message(GB_gameboy_t *gb, const char *message, GB_log_attributes_t attributes)
{
    (void)attributes;
    Peer *p = GB_get_user_data(gb);
    if (strstr(message, "while using internal clock")) p->collisions++;
    else fputs(message, stderr);
}
void pair_free(Pair *pair)
{
    if (!pair) return;
    for (int i = 0; i < 2; i++) if (pair->peers[i].gb) GB_dealloc(pair->peers[i].gb);
    free(pair);
}
Pair *pair_new(const char *rom, const char *boot)
{
    Pair *pair = calloc(1, sizeof(*pair));
    if (!pair) return NULL;
    for (int i = 0; i < 2; i++) {
        Peer *p = &pair->peers[i];
        p->pair = pair; p->index = i; p->outgoing = true;
        p->gb = GB_alloc();
        if (!p->gb) { pair_free(pair); return NULL; }
        GB_init(p->gb, GB_MODEL_CGB_E);
        if (GB_load_rom(p->gb, rom) || GB_load_boot_rom(p->gb, boot)) {
            pair_free(pair); return NULL;
        }
        GB_set_user_data(p->gb, p);
        GB_set_log_callback(p->gb, log_message);
        GB_set_rgb_encode_callback(p->gb, rgb);
        GB_set_pixels_output(p->gb, p->pixels);
        GB_set_turbo_mode(p->gb, true, true);
        GB_set_turbo_cap(p->gb, 0);
        GB_set_serial_transfer_bit_start_callback(p->gb, serial_start);
        GB_set_serial_transfer_bit_end_callback(p->gb, serial_end);
    }
    /* Independent power-on times: do not phase-lock both LCDs and their
     * VBlank-driven attempts to become cable clock master. */
    pair->peers[1].cycles = 140448 / 4;
    return pair;
}
void pair_tick(Pair *pair, unsigned frames)
{
    pair->target += (uint64_t)frames * 140448;
    while (pair->peers[0].cycles < pair->target || pair->peers[1].cycles < pair->target) {
        Peer *p = &pair->peers[pair->peers[0].cycles > pair->peers[1].cycles];
        p->cycles += GB_run(p->gb);
    }
}
void pair_keys(Pair *pair, unsigned peer, unsigned mask)
{
    GB_set_key_mask(pair->peers[peer].gb, mask);
}
uint8_t pair_read(Pair *pair, unsigned peer, unsigned bank, unsigned address)
{
    GB_gameboy_t *gb = pair->peers[peer].gb;
    if (address >= 0xa000 && address < 0xc000) {
        size_t size; uint16_t active;
        const uint8_t *ram = GB_get_direct_access(gb, GB_DIRECT_ACCESS_CART_RAM, &size, &active);
        unsigned offset = bank * 0x2000 + address - 0xa000;
        return offset < size ? ram[offset] : 0xff;
    }
    if (address >= 0xc000 && address < 0xe000) {
        size_t size; uint16_t active;
        const uint8_t *ram = GB_get_direct_access(gb, GB_DIRECT_ACCESS_RAM, &size, &active);
        unsigned offset = address < 0xd000 ? address - 0xc000 : bank * 0x1000 + address - 0xd000;
        return offset < size ? ram[offset] : 0xff;
    }
    return GB_read_memory(gb, address);
}
const uint32_t *pair_pixels(Pair *pair, unsigned peer) { return pair->peers[peer].pixels; }
uint64_t pair_bits(Pair *pair, unsigned peer) { return pair->peers[peer].bits; }
uint64_t pair_collisions(Pair *pair, unsigned peer) { return pair->peers[peer].collisions; }
unsigned pair_pc(Pair *pair, unsigned peer) { return GB_get_registers(pair->peers[peer].gb)->pc; }
int pair_save(Pair *pair, unsigned peer, const char *path) { return GB_save_battery(pair->peers[peer].gb, path); }
int pair_load(Pair *pair, unsigned peer, const char *path) { return GB_load_battery(pair->peers[peer].gb, path); }
