from constructs import Construct
from aws_cdk import (
    aws_ec2 as ec2,
    aws_autoscaling as autoscaling,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_assets as s3assets,
    aws_glue_alpha as glue_alpha,
    aws_kinesis as kinesis,
    Aws,
)

from math import ceil

class AUTOSCALING(Construct):
    def __init__(self, scope: Construct, id_: str, 
        instance_type: str,
        capacity: int,
        key_name: str,
        kinesis_data_stream: kinesis.Stream, 
        glue_job: glue_alpha.Job, 
        glue_worker_count: int, 
        bucket: s3.Bucket) -> None:

        super().__init__(scope, id_)


        vpc = ec2.Vpc(self, 'VPC',
            vpc_name='glue-benchmark-vpc',
            cidr=f'10.1.0.0/16',
            subnet_configuration=[
                    {
                        'cidrMask': 24,
                        'name': f'Subnet',
                        'subnetType': ec2.SubnetType.PUBLIC,
                    },
            ],
        )


        security_group = ec2.SecurityGroup(self, 'Security-Group',
            vpc=vpc,
            allow_all_outbound=True,
        )
        security_group.add_ingress_rule (
            peer=ec2.Peer.ipv4('0.0.0.0/0'),
            connection=ec2.Port.tcp(22),
            description='allow ssh from anywhere',                
        )



        bench_script_filename = 'bench_loop.sh'

        asset_bench_loop_shell_script = s3assets.Asset(self, 'bench-shell-script',
            path=bench_script_filename,
        )


        produce_rps_min = ceil(30000 / capacity) # ceil(((glue_worker_count * 1000) - 5000) / capacity)
        produce_rps_step = ceil(1000 / capacity)
        produce_rps_max = ceil(50000 / capacity) + produce_rps_step # ceil(((glue_worker_count * 1000) + 6000) / capacity)


        multipart_user_data = ec2.MultipartUserData()
        user_data = ec2.UserData.for_linux()
        multipart_user_data.add_user_data_part(user_data=user_data, content_type=ec2.MultipartBody.SHELL_SCRIPT, make_default=True)
        multipart_user_data.add_commands(
            'yum update -y',
            'yum install -y java-1.8.0-openjdk-devel git',
            'yum remove -y java-1.7.0-openjdk',

            'wget https://dlcdn.apache.org/maven/maven-3/3.8.4/binaries/apache-maven-3.8.4-bin.tar.gz',
            'tar xvf apache-maven-3.8.4-bin.tar.gz',
            'mv apache-maven-3.8.4  /usr/local/apache-maven',
            'rm apache-maven-3.8.4-bin.tar.gz',

            'echo export M2_HOME=/usr/local/apache-maven >> /home/ec2-user/.bashrc',
            'echo export M2=\\$M2_HOME/bin >> /home/ec2-user/.bashrc',
            'echo export PATH=\\$M2:$PATH >> /home/ec2-user/.bashrc',

            f'echo export GLUE_JOB_NAME={glue_job.job_name} >> /home/ec2-user/.bashrc',
            f'echo export GLUE_WORKERS={glue_worker_count} >> /home/ec2-user/.bashrc',
            f'echo export KINESIS_DATASTREAM={kinesis_data_stream.stream_name} >> /home/ec2-user/.bashrc',
            f'echo export AWS_DEFAULT_REGION={Aws.REGION} >> /home/ec2-user/.bashrc',

            f'echo export PRODUCER_RPS_MIN={produce_rps_min} >> /home/ec2-user/.bashrc',
            f'echo export PRODUCER_RPS_MAX={produce_rps_max} >> /home/ec2-user/.bashrc',
            f'echo export PRODUCER_RPS_STEP={produce_rps_step} >> /home/ec2-user/.bashrc',

            'git clone https://github.com/fibert/amazon-kinesis-producer.git /home/ec2-user/amazon-kinesis-producer',
            'cd /home/ec2-user/amazon-kinesis-producer/java/amazon-kinesis-producer-sample',
            
            
            f'aws s3 cp {asset_bench_loop_shell_script.s3_object_url} .',
            f"chmod u+x ./{asset_bench_loop_shell_script.s3_object_key.split('/')[-1]}",

            'chown -R ec2-user: /home/ec2-user/amazon-kinesis-producer',

            # f"./{asset_bench_loop_shell_script.s3_object_key.split('/')[-1]}",
            # f"aws s3 cp output-loop s3://fibertdf-spark-ui-logs/output-loop-{glue_worker_count}",
        )


        self.autoscaling_group = autoscaling.AutoScalingGroup(self, "AutoScalingGroup",
            instance_type=ec2.InstanceType(instance_type),
            machine_image=ec2.MachineImage.latest_amazon_linux(),
            vpc=vpc,
            security_group=security_group,
            key_name=key_name,
            user_data=user_data,
            min_capacity=capacity,
            desired_capacity=capacity,
            max_capacity=capacity,
        )

        kinesis_data_stream.grant_read_write(self.autoscaling_group.role)
        bucket.grant_read_write(self.autoscaling_group.role)
        asset_bench_loop_shell_script.grant_read(self.autoscaling_group.role)

       
        cloudwatch_policy = iam.Policy(self, 'cloudwatch-policy',
            document=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        actions=[
                            'cloudwatch:PutMetricData'
                        ],
                        effect=iam.Effect.ALLOW,
                        resources=['*'],
                    ),
                    iam.PolicyStatement(
                        actions=[
                            'glue:*'
                        ],
                        effect=iam.Effect.ALLOW,
                        resources=[glue_job.job_arn],
                    )
                ],
            ),
            policy_name='KPL-instance-policy',
            roles=[self.autoscaling_group.role],
        )


            # export AWS_DEFAULT_REGION=us-east-1
            # 'cd ~/amazon-kinesis-producer/java/amazon-kinesis-producer-sample/',
            # f'echo GLUE_WORKERS={glue_worker_count} >> ~/.bashrc',
            # f'echo KINESIS_DATASTREAM={kinesis_data_stream.stream_name} >> ~/.bashrc'
            # 'echo export GLUE_WORKERS >> ~/.bashrc'
            # 'echo export KINESIS_DATASTREAM >> ~/.bashrc'
            # f"aws s3 cp {bucket.s3_url_for_object}/bench_script.sh .",
            # 'chmod u+x bench_script.sh',
            # f"bench_script.sh {kinesis_data_stream.stream_name} {glue_worker_count}",
            
            # curl http://169.254.169.254/latest/user-data | bash && source ~/.bashrc && cd amazon-kinesis-producer/java/amazon-kinesis-producer-sample/