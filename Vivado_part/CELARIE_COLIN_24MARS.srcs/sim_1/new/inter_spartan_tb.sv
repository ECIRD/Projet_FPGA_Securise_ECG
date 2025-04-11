`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 14.03.2025 14:00:33
// Design Name: 
// Module Name: inter_spartan_tb
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module inter_spartan_tb(

    );
    logic clock_i;
    logic reset_i;
    logic Rx_i;
    logic Baud_i;
    logic Tx_o;
    logic Baud_o;
    logic RTS_o;
    inter_spartan IS(
        .clock_i(clock_i),  //main clock
        .reset_i(reset_i),  //asynchronous reset active low
        .Rx_i(Rx_i),     //RX to RS232
        .Baud_i(Baud_i),   //baud selection
        .Tx_o(Tx_o),     //Tx to RS 232
        .Baud_o(Baud_o),
        .RTS_o(RTS_o)
    );
    always #10 clock_i = ~clock_i;
    initial begin
        clock_i = 1'b0;
        reset_i = 1'b0;
        Rx_i = 1'b0;
        Baud_i = 1'b0;
    end
endmodule
