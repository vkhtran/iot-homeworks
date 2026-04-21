# Build a More Efficient Watering Cycle

## Objective

The goal of this assignment is to improve the watering logic so that the pump does not always run for a fixed amount of time. Instead, the watering duration should be calculated from calibration data.

Because I am using virtual IoT hardware, I followed the assignment guidance to simulate the effect of watering by changing the soil moisture reading by a fixed amount per second while the relay is on.

## Simulated Calibration Method

I started with a dry-soil reading in the virtual device. Then I simulated watering in 1-second steps. After each step, I used a stabilized soil moisture reading before recording the next value.

To keep the simulation consistent, I assumed that each second of watering would reduce the soil moisture reading by about 19 to 21 points. This matches the assignment requirement for using fixed amounts of water and is appropriate for a virtual hardware setup.

## Calibration Data

| Total Pump Time | Soil Moisture | Decrease |
| --- | ---: | ---: |
| Dry | 648 | 0 |
| 1s | 627 | 21 |
| 2s | 607 | 20 |
| 3s | 586 | 21 |
| 4s | 567 | 19 |
| 5s | 547 | 20 |
| 6s | 526 | 21 |

## Average Change Per Second

The decrease after each second of watering is:

- 21
- 20
- 21
- 19
- 20
- 21

The average decrease per second is:

```text
(21 + 20 + 21 + 19 + 20 + 21) / 6 = 20.33
```

This means that, in this virtual calibration, each second of watering reduces the soil moisture reading by about 20.33.

## Target Moisture Level

The lesson explains that the desired soil moisture range is around 400 to 450. I selected the following target:

```text
target_soil_moisture = 430
```

This is the center of the recommended range and gives a practical watering target.

## Improved Watering Logic

Before calibration, the server watered for a fixed 5 seconds whenever the soil moisture reading was too high. This could overwater the plant if the soil only needed a small correction.

After calibration, the watering time is calculated dynamically:

```text
water_time = ceil((current_soil_moisture - target_soil_moisture) / 20.33)
```

If the current reading is already at or below the target, the pump stays off.

### Example

If the current soil moisture reading is 470:

```text
470 - 430 = 40
40 / 20.33 = 1.97
ceil(1.97) = 2
```

So the pump should run for 2 seconds.

## Updated Server Behavior

The server code was updated to:

1. Receive `soil_moisture` telemetry from MQTT.
2. Calculate the moisture gap from the target value.
3. Convert that gap into a watering duration using the calibration average.
4. Turn the relay on for the calculated number of seconds.
5. Turn the relay off.
6. Wait 20 seconds for the soil moisture reading to stabilize.
7. Subscribe to telemetry again after the watering cycle is complete.

The server also applies a safety cap:

```text
max_water_time = 10
```

This prevents the pump from running too long in one cycle if a very dry reading is received.

## Code Configuration

The updated server uses the following calibrated values:

```python
wait_time = 20
target_soil_moisture = 430
moisture_drop_per_second = 20.33
max_water_time = 10
```

## Conclusion

This assignment shows that a calibrated watering cycle is more efficient than a fixed-duration watering cycle. Even in a virtual hardware setup, using a consistent simulated dataset allows the server to make better watering decisions.

The improved solution:

- reduces unnecessary watering,
- keeps the soil closer to the target range,
- and matches the assignment requirement to use calibration data to improve the server logic.

For a real deployment, the same method should be repeated with measured sensor data from the actual soil, pump, and sensor setup.
