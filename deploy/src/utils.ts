import { TezosToolkit } from "@taquito/taquito";
import fs = require("fs");

export const loadContract = (filename: string): string => {
  const contractFile = filename;
  const contract = fs.readFileSync(contractFile).toString();
  return contract;
};

export const deployContract = async (code: string, storage: string, tezos: TezosToolkit): Promise<string | boolean> => {
  try {
    const originOp = await tezos.contract.originate({
      code: code,
      init: storage,
    });

    await originOp.confirmation(1);
    return originOp.contractAddress as string;
  } catch (err) {
    console.log(err);
    return false;
  }
};
