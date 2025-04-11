`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 07.03.2025 16:02:15
// Design Name: 
// Module Name: counter_block
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


module counter_block(
        input logic en_cpt_i,
        input logic reset_i,
        input logic init_cpt_i,
        input logic clock_i,
        output logic [4:0]counter_o
    );
    logic [4:0] counter;
    
    always_ff @(posedge clock_i or negedge reset_i) begin
        if (reset_i == 1'b0) begin
            counter <= 5'h00000;
        end
        else begin
            if (en_cpt_i == 1'b1) begin
                if (init_cpt_i == 1'b0) counter <= counter + 1;
                else counter <= 5'h00000;
            end
            else counter <= counter;
        end
    end
    assign counter_o = counter;
endmodule
