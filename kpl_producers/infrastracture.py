import os
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

import config

class AutoScaling(Construct):
    def __init__(self, scope: Construct, id_: str, 
        kinesis_data_stream: kinesis.Stream, 
        glue_job: glue_alpha.Job, 
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



        bench_script_filename = f'{os.path.dirname(os.path.abspath(__file__))}/scripts/bench_loop.sh'

        asset_bench_loop_shell_script = s3assets.Asset(self, 'bench-shell-script',
            path=bench_script_filename,
        )

        bashrc_path = '/root/.bashrc' # '/home/ec2-user/.bashrc'

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

            f'echo export M2_HOME=/usr/local/apache-maven >> {bashrc_path}',
            f'echo export M2=\\$M2_HOME/bin >> {bashrc_path}',
            f'echo export PATH=\\$M2:$PATH >> {bashrc_path}',

            f'echo export GLUE_JOB_NAME={glue_job.job_name} >> {bashrc_path}',
            f'echo export GLUE_WORKERS={config.GLUE_JOB_WORKERS} >> {bashrc_path}',
            f'echo export KINESIS_DATASTREAM={kinesis_data_stream.stream_name} >> {bashrc_path}',
            f'echo export AWS_DEFAULT_REGION={Aws.REGION} >> {bashrc_path}',

            f'echo export PRODUCER_RPS_MIN={config.EC2_PRODUCER_RPS_MIN} >> {bashrc_path}',
            f'echo export PRODUCER_RPS_MAX={config.EC2_PRODUCER_RPS_MAX} >> {bashrc_path}',
            f'echo export PRODUCER_RPS_STEP={config.EC2_PRODUCER_RPS_STEP} >> {bashrc_path}',
            f'echo export PRODUCER_RUNNING_TIME={config.EC2_PRODUCER_RUNNING_TIME} >> {bashrc_path}',

            f'source {bashrc_path}',

            'git clone https://github.com/fibert/amazon-kinesis-producer.git',
            'cd amazon-kinesis-producer/java/amazon-kinesis-producer-sample',
            
            
            f'aws s3 cp {asset_bench_loop_shell_script.s3_object_url} ./bench_loop.sh',
            f"chmod u+x ./bench_loop.sh",

            './bench_loop.sh',    
        )


        self.autoscaling_group = autoscaling.AutoScalingGroup(self, "Autoscaling",
            instance_type=ec2.InstanceType(config.AUTOSCALING_GROUP_INSTANCE_TYPE),
            machine_image=ec2.MachineImage.latest_amazon_linux(),
            vpc=vpc,
            security_group=security_group,
            key_name=config.AUTOSCALING_EC2_KEY_PAIR_NAME,
            user_data=user_data,
            min_capacity=config.AUTOSCALING_GROUP_CAPACITY,
            desired_capacity=config.AUTOSCALING_GROUP_CAPACITY,
            max_capacity=config.AUTOSCALING_GROUP_CAPACITY,
        )

        kinesis_data_stream.grant_read_write(self.autoscaling_group.role)
        bucket.grant_read_write(self.autoscaling_group.role)
        asset_bench_loop_shell_script.grant_read(self.autoscaling_group.role)
        
        self.autoscaling_group.role.attach_inline_policy(
            iam.Policy(self, 'kpl-publish-cloudwatch-policy',
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
            )
        )