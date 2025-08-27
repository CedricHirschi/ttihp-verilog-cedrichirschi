/*
 * Copyright (c) 2024 Cedric Hirschi
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_cedrichirschi_sar #(
  parameter integer Resolution = 8 // Resolution of the ADC in bits
) (
  input  logic [7:0] ui_in,    // Dedicated inputs
  output logic [7:0] uo_out,   // Dedicated outputs
  input  logic [7:0] uio_in,   // IOs: Input path
  output logic [7:0] uio_out,  // IOs: Output path
  output logic [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
  input  logic       ena,      // always 1 when the design is powered, so you can ignore it
  input  logic       clk,      // clock
  input  logic       rst_n     // reset_n - low to reset
);
  logic start_i;
  logic comp_i;
  logic [Resolution-1:0] dac_o;
  logic [Resolution-1:0] data_o;

  sar # (
    .RESOLUTION(Resolution)
  )
  sar_inst (
    .clk_i(clk),
    .rst_ni(rst_n),

    .start_i(start_i),
    .comp_i(comp_i),

    .dac_o(dac_o),
    .rdy_o(),
    .result_o(data_o)
  );

  assign {comp_i, start_i} = ui_in[1:0];

  assign uo_out = dac_o;
  assign uio_out = data_o;
  assign uio_oe = {Resolution{1'b1}}; // Enable all IOs as outputs

  logic _unused = |{ui_in[7:2], uio_in}; // Prevent unused signal warnings
endmodule
