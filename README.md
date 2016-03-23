# market-mania
Executes a simple trading strategy on an equity, provides results based on several assumptions

Command line interface:
1) Enter the equity's symbol--this should match the file name
2) Enter the span--this is measured in weeks and is the length of the trailing envelope used to determine the relative
   high and relative low during the period
3) Span percent--determines when to buy equity, for example, if the low within the given span is 10, and the high
   is 20, a span percent of 0.5 would buy the equity when the price is 15 or lower.
4) Limit (entered as a percent)--This is the amount the equity must increase by before the limit is lifted. The selling
   price will trail at this number.
5) Eject (entered as a percent)--This is the panic selling number. If the equity loses this amount, a sale is triggered
6) Initial Balance--The amount of the original investment (note: model assumes fractional ownership of shares)

The CSV files must follow the following format (this format is provided at www.nasdaq.com):

date,close,volume,open,high,low
