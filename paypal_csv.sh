#!/bin/bash
# Simple awk to convert the Paypal CSV to the bulk loader format.

awk -F , '$6 ~ "Completed" {print $1","$4","$7","$8","$9","$10","$12}' $1 > $1.clean
