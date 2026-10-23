/* A deterministic HID handle-lifetime test backend. No physical devices. */
#define _DEFAULT_SOURCE
#include <hidapi.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <unistd.h>
struct hid_device_ { atomic_int active, closed; };
static atomic_int active, violations, opens;
int test_active(void) { return atomic_load(&active); }
int test_violations(void) { return atomic_load(&violations); }
int test_opens(void) { return atomic_load(&opens); }
hid_device *hid_open(unsigned short v, unsigned short p, const wchar_t *s) {
    atomic_fetch_add(&opens,1); usleep(20000);
    return calloc(1,sizeof(hid_device));
}
hid_device *hid_open_path(const char *path) { return hid_open(0,0,NULL); }
void hid_close(hid_device *d) {
    if (!d) return;
    if (atomic_load(&d->active) || atomic_exchange(&d->closed,1))
        atomic_fetch_add(&violations,1);
    /* Retain the tiny fixture handle so a stale-pointer call is detectable. */
}
int hid_write(hid_device *d,const unsigned char *buf,size_t n) {
    if (!d || atomic_load(&d->closed)) { atomic_fetch_add(&violations,1); return -1; }
    atomic_fetch_add(&d->active,1); atomic_fetch_add(&active,1);
    usleep(50000);
    if (atomic_load(&d->closed)) atomic_fetch_add(&violations,1);
    atomic_fetch_sub(&d->active,1); atomic_fetch_sub(&active,1);
    return (int)n;
}
int hid_read(hid_device *d,unsigned char *buf,size_t n) {
    int rc=hid_write(d,buf,n); if (rc>0) buf[0]=68; return rc>0 ? 1 : rc;
}
int hid_read_timeout(hid_device *d,unsigned char *b,size_t n,int ms) { return hid_read(d,b,n); }
int hid_set_nonblocking(hid_device *d,int x) { return d && !atomic_load(&d->closed) ? 0 : -1; }
int hid_send_feature_report(hid_device *d,const unsigned char *b,size_t n) { return hid_write(d,b,n); }
int hid_get_feature_report(hid_device *d,unsigned char *b,size_t n) { return hid_read(d,b,n); }
int hid_get_input_report(hid_device *d,unsigned char *b,size_t n) { return hid_read(d,b,n); }
const wchar_t *hid_error(hid_device *d) { return L"fixture"; }
