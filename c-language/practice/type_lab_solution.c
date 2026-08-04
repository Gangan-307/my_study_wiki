#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

bool int32_to_u8_checked(int32_t input, uint8_t *output)
{
    if ((output == NULL) || (input < 0) || (input > (int32_t)UINT8_MAX)) {
        return false;
    }

    *output = (uint8_t)input;
    return true;
}

bool parse_sensor_frame(const uint8_t *frame, size_t length,
                        uint16_t *voltage_raw, int16_t *temperature_raw)
{
    uint16_t voltage;
    uint16_t temperature_bits;
    int32_t temperature;

    if ((frame == NULL) || (voltage_raw == NULL) ||
        (temperature_raw == NULL) || (length != 4U)) {
        return false;
    }

    voltage = ((uint16_t)frame[0] << 8U) | (uint16_t)frame[1];
    temperature_bits = ((uint16_t)frame[2] << 8U) | (uint16_t)frame[3];

    if ((temperature_bits & 0x8000U) != 0U) {
        temperature = (int32_t)temperature_bits - 65536;
    } else {
        temperature = (int32_t)temperature_bits;
    }

    *voltage_raw = voltage;
    *temperature_raw = (int16_t)temperature;
    return true;
}

bool has_elapsed(uint32_t now, uint32_t start, uint32_t timeout_ms)
{
    return (now - start) >= timeout_ms;
}

bool is_valid_length(int16_t length, uint16_t capacity)
{
    return (length >= 0) && ((uint16_t)length <= capacity);
}

uint16_t scale_adc(uint16_t raw)
{
    if (raw > 4095U) {
        raw = 4095U;
    }

    return (uint16_t)(((uint32_t)raw * 1000U) / 4095U);
}

static void check_bool(const char *name, bool actual, bool expected,
                       unsigned int *failures)
{
    if (actual == expected) {
        printf("[PASS] %s\n", name);
    } else {
        printf("[FAIL] %s: actual=%d expected=%d\n", name,
               (int)actual, (int)expected);
        ++(*failures);
    }
}

static void test_checked_conversion(unsigned int *failures)
{
    uint8_t output = 99U;

    check_bool("convert 0", int32_to_u8_checked(0, &output), true, failures);
    check_bool("convert 0 value", output == 0U, true, failures);

    output = 99U;
    check_bool("convert 255", int32_to_u8_checked(255, &output), true, failures);
    check_bool("convert 255 value", output == UINT8_MAX, true, failures);

    output = 99U;
    check_bool("reject -1", int32_to_u8_checked(-1, &output), false, failures);
    check_bool("reject -1 preserves output", output == 99U, true, failures);

    output = 99U;
    check_bool("reject 256", int32_to_u8_checked(256, &output), false, failures);
    check_bool("reject 256 preserves output", output == 99U, true, failures);
}

static void test_sensor_frame(unsigned int *failures)
{
    const uint8_t frame[4] = {0x01U, 0x2CU, 0xFEU, 0xD4U};
    uint16_t voltage = 0U;
    int16_t temperature = 0;

    check_bool("parse sensor frame",
               parse_sensor_frame(frame, sizeof(frame), &voltage, &temperature),
               true, failures);
    check_bool("voltage is 300", voltage == 300U, true, failures);
    check_bool("temperature is -300", temperature == -300, true, failures);

    voltage = 123U;
    temperature = 456;
    check_bool("reject short frame",
               parse_sensor_frame(frame, 3U, &voltage, &temperature), false, failures);
    check_bool("short frame preserves voltage", voltage == 123U, true, failures);
    check_bool("short frame preserves temperature", temperature == 456, true, failures);
}

static void test_timer_wraparound(unsigned int *failures)
{
    check_bool("elapsed at boundary", has_elapsed(150U, 100U, 50U), true, failures);
    check_bool("not elapsed", has_elapsed(149U, 100U, 50U), false, failures);
    check_bool("elapsed after wrap",
               has_elapsed(20U, UINT32_MAX - 9U, 30U), true, failures);
}

static void test_challenge(unsigned int *failures)
{
    check_bool("negative length is invalid", is_valid_length(-1, 128U), false, failures);
    check_bool("valid length", is_valid_length(128, 128U), true, failures);
    check_bool("too large length", is_valid_length(129, 128U), false, failures);
    check_bool("ADC zero", scale_adc(0U) == 0U, true, failures);
    check_bool("ADC full scale", scale_adc(4095U) == 1000U, true, failures);
    check_bool("ADC input is clamped", scale_adc(5000U) == 1000U, true, failures);
}

int main(void)
{
    unsigned int failures = 0U;

    test_checked_conversion(&failures);
    test_sensor_frame(&failures);
    test_timer_wraparound(&failures);
    test_challenge(&failures);

    printf("\nTotal failures: %u\n", failures);
    return (failures == 0U) ? 0 : 1;
}
