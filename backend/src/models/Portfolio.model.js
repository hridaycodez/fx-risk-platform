const mongoose = require('mongoose');

const portfolioSchema = new mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true,
    },
    name: {
      type: String,
      required: true,
      trim: true,
      maxlength: 100,
    },
    baseCurrency: {
      type: String,
      enum: ['EUR', 'USD', 'GBP', 'INR', 'AED', 'JPY', 'CHF'],
      default: 'EUR',
    },
    exposures: [
      {
        name: { type: String, required: true, trim: true },
        expType: {
          type: String,
          enum: ['revenue', 'cost'],
          required: true,
        },
        amount: {
          type: Number,
          required: true,
          min: 0,
        },
        currency: {
          type: String,
          enum: ['EUR', 'USD', 'GBP', 'INR', 'AED', 'JPY', 'CHF'],
          required: true,
        },
      },
    ],
  },
  { timestamps: true }
);

module.exports = mongoose.model('Portfolio', portfolioSchema);
