import { STSClient, GetCallerIdentityCommand } from "@aws-sdk/client-sts";

export interface PartitionInfo {
  partition: string;
  defaultRegion: string;
}

/**
 * Detects the AWS partition (aws, aws-us-gov, or aws-cn) by examining the caller identity ARN.
 * This enables CFAT to automatically operate in the correct partition without hardcoded regions.
 *
 * @param region - Optional region to use for the STS client (defaults to 'us-east-1')
 * @returns PartitionInfo containing the detected partition and its default region
 */
export async function getPartitionInfo(region: string = 'us-east-1'): Promise<PartitionInfo> {
  const client = new STSClient({ region });

  try {
    const response = await client.send(new GetCallerIdentityCommand({}));
    const arn = response.Arn || '';

    // AWS GovCloud partition
    if (arn.includes(':aws-us-gov:')) {
      console.log('Detected AWS GovCloud partition (aws-us-gov)');
      return { partition: 'aws-us-gov', defaultRegion: 'us-gov-west-1' };
    }
    // AWS China partition
    else if (arn.includes(':aws-cn:')) {
      console.log('Detected AWS China partition (aws-cn)');
      return { partition: 'aws-cn', defaultRegion: 'cn-north-1' };
    }

    // Standard AWS partition (default)
    console.log('Detected standard AWS partition (aws)');
    return { partition: 'aws', defaultRegion: 'us-east-1' };

  } catch (error) {
    console.error('Error detecting partition, defaulting to standard AWS partition:', error);
    return { partition: 'aws', defaultRegion: 'us-east-1' };
  } finally {
    client.destroy();
  }
}

export default getPartitionInfo;
