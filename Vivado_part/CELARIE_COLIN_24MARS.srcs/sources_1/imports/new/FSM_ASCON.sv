`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 07.03.2025 14:27:42
// Design Name: 
// Module Name: FSM_ASCON
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


module FSM_ASCON (
    // inputs/outpus/ declaration
    input  logic         clock_i,
    input  logic         reset_i,
    input logic [4:0] cpt_i,
    input logic         go_i,
    input logic         end_associate_i,
    input logic         cipher_valid_i,
    input logic         end_tag_i,
    input logic         end_initialisation_i,
    input logic         end_cipher_i,
    
    output  logic       init_o,
    output  logic       associate_data_o,
    output  logic       finalisation_o,
    output  logic       data_valid_o,
    output  logic       en_cpt_o,
    output  logic       init_cpt_o,
    output logic        init_cipher_o,
    output logic        en_cipher_reg_o

);

  // state list
  typedef enum {
    idle,
    start,
    idle_start,
    associate_start,
    idle_associate,
    cipher_start,
    enable_cipher_1,//
    enable_cipher_2,// Etats permettant de piloter l'écriture dans le registre u_ascon_reg dans inter_spartan
    enable_cipher_3,//
    idle_cipher,
    finalisation_start,  //jbr
    idle_finalisation,
    idle_end 
    //counter_add
  } State_t;

  // Present and futur states declaration
  State_t Ep, Ef;
/*  
  ila_1 FSM_State (
	.clk(clock_i), // input wire clk


	.probe0(Ep), // input wire [31:0]  probe0  
	.probe1(Ef) // input wire [31:0]  probe1
);
*/
  always_ff @(posedge clock_i, negedge reset_i) begin
    if (reset_i == 1'b0) begin
      Ep <= idle;
    end else begin
      Ep <= Ef;
    end
  end
  
  
  always_comb begin
    case (Ep)
    idle:
        if (go_i == 1'b1) Ef = start;
        else Ef = idle;
    start:
        Ef = idle_start;
    idle_start:
        if (end_initialisation_i == 1'b1) Ef = associate_start;
        else Ef = idle_start;
    associate_start:
        Ef = idle_associate;
    idle_associate:
        if (end_associate_i == 1'b1) Ef = cipher_start;
        else Ef = idle_associate;
    cipher_start:
       // Ef = counter_add;
  //  counter_add :
        Ef = idle_cipher;
    enable_cipher_1: Ef = cipher_start;
    idle_cipher:
        if (end_cipher_i == 1'b0) Ef = idle_cipher;
        else begin
            if (cpt_i < 5'h16) Ef = enable_cipher_1;
            else Ef = finalisation_start;
        end
    finalisation_start:
        Ef = enable_cipher_2;
    enable_cipher_2:
        Ef = idle_finalisation;
    idle_finalisation:
        if (end_tag_i == 1'b1) Ef = enable_cipher_3;
        else Ef = idle_finalisation;
    enable_cipher_3: Ef = idle_end;
    idle_end:
        if (go_i == 1'b0) Ef = idle;
        else Ef = idle_end;
    default: Ef = idle; 
    endcase
    
  end
  always_comb begin

    case (Ep)
      idle: begin
        init_o = 1'b0;
        associate_data_o = 1'b0;
        finalisation_o = 1'b0;
        data_valid_o = 1'b0;
        init_cpt_o = 1'b1;
        en_cpt_o = 1'b1;
        init_cipher_o = 1'b0;
        en_cipher_reg_o = 1'b0;
      end
      start: begin
        init_o = 1'b1;
        associate_data_o = 1'b0;
        finalisation_o = 1'b0;
        data_valid_o = 1'b0;
        init_cpt_o = 1'b1;
        en_cpt_o = 1'b1;
        init_cipher_o = 1'b1;
        en_cipher_reg_o = 1'b1;
      end
      idle_start: begin
        init_o = 1'b0;
        associate_data_o = 1'b0;
        finalisation_o = 1'b0;
        data_valid_o = 1'b0;
        init_cpt_o = 1'b0;
        en_cpt_o = 1'b0;
        init_cipher_o = 1'b0;
        en_cipher_reg_o = 1'b0;
      end
      associate_start: begin
        init_o = 1'b0;
        associate_data_o = 1'b1;
        finalisation_o = 1'b0;
        data_valid_o = 1'b1;
        init_cpt_o = 1'b0;
        en_cpt_o = 1'b0;
        init_cipher_o = 1'b0;
        en_cipher_reg_o = 1'b0;
      end
      idle_associate: begin
        init_o = 1'b0;
        associate_data_o = 1'b0;
        finalisation_o = 1'b0;
        data_valid_o = 1'b0;
        init_cpt_o = 1'b0;
        en_cpt_o = 1'b0;
        init_cipher_o = 1'b0;
        en_cipher_reg_o = 1'b0;
      end
      cipher_start: begin
        init_o = 1'b0;
        associate_data_o = 1'b0;
        finalisation_o = 1'b0;
        data_valid_o = 1'b1;
        init_cpt_o = 1'b0;
        en_cpt_o = 1'b1;
        init_cipher_o = 1'b0;
        en_cipher_reg_o = 1'b0;
      end
      enable_cipher_1: begin
        init_o = 1'b0;
        associate_data_o = 1'b0;
        finalisation_o = 1'b0;
        data_valid_o = 1'b0;
        init_cpt_o = 1'b0;
        en_cpt_o = 1'b0;
        init_cipher_o = 1'b0;
        en_cipher_reg_o = 1'b1;
      end
        
     /* counter_add: begin
        init_o = 1'b0;
        associate_data_o = 1'b0;
        finalisation_o = 1'b0;
        data_valid_o = 1'b0;
        init_cpt_o = 1'b0;
        en_cpt_o = 1'b1;
      end*/
      idle_cipher: begin
        init_o = 1'b0;
        associate_data_o = 1'b0;
        finalisation_o = 1'b0;
        data_valid_o = 1'b0;
        init_cpt_o = 1'b0;
        en_cpt_o = 1'b0;
        init_cipher_o = 1'b0;
        en_cipher_reg_o = 1'b0;
      end
      finalisation_start: begin
        init_o = 1'b0;
        associate_data_o = 1'b0;
        finalisation_o = 1'b1;
        data_valid_o = 1'b1;
        init_cpt_o = 1'b0;
        en_cpt_o = 1'b1;
        init_cipher_o = 1'b0;
        en_cipher_reg_o = 1'b0;
      end
      enable_cipher_2: begin
        init_o = 1'b0;
        associate_data_o = 1'b0;
        finalisation_o = 1'b0;
        data_valid_o = 1'b0;
        init_cpt_o = 1'b0;
        en_cpt_o = 1'b0;
        init_cipher_o = 1'b0;
        en_cipher_reg_o = 1'b1;
      end
      idle_finalisation: begin
        init_o = 1'b0;
        associate_data_o = 1'b0;
        finalisation_o = 1'b0;
        data_valid_o = 1'b0;
        init_cpt_o = 1'b0;
        en_cpt_o = 1'b0;
        init_cipher_o = 1'b0;
        en_cipher_reg_o = 1'b0;
      end
      enable_cipher_3: begin
        init_o = 1'b0;
        associate_data_o = 1'b0;
        finalisation_o = 1'b0;
        data_valid_o = 1'b0;
        init_cpt_o = 1'b0;
        en_cpt_o = 1'b0;
        init_cipher_o = 1'b0;
        en_cipher_reg_o = 1'b1;
      end
      idle_end: begin
        init_o = 1'b0;
        associate_data_o = 1'b0;
        finalisation_o = 1'b0;
        data_valid_o = 1'b0;
        init_cpt_o = 1'b0;
        en_cpt_o = 1'b0;
        init_cipher_o = 1'b0;
        en_cipher_reg_o = 1'b0;
      end
    endcase
    
  end  
endmodule : FSM_ASCON