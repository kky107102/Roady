package com.blockai.roady.robot.config;

import com.blockai.roady.robot.mqtt.RobotMqttTopics;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.integration.annotation.ServiceActivator;
import org.springframework.integration.channel.DirectChannel;
import org.springframework.integration.config.EnableIntegration;
import org.springframework.integration.core.MessageProducer;
import org.springframework.integration.mqtt.core.DefaultMqttPahoClientFactory;
import org.springframework.integration.mqtt.core.MqttPahoClientFactory;
import org.springframework.integration.mqtt.inbound.MqttPahoMessageDrivenChannelAdapter;
import org.springframework.integration.mqtt.outbound.MqttPahoMessageHandler;
import org.springframework.integration.mqtt.support.DefaultPahoMessageConverter;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.MessageHandler;

@Configuration
@EnableIntegration
public class MqttConfig {

    @Value("${mqtt.broker-ip:localhost}")
    private String brokerIp;

    @Value("${mqtt.broker-port:1883}")
    private String brokerPort;

    /**
     * MQTT Broker 연결 설정
     */
    @Bean
    public MqttPahoClientFactory mqttClientFactory() {

        DefaultMqttPahoClientFactory factory =
                new DefaultMqttPahoClientFactory();

        MqttConnectOptions options = new MqttConnectOptions();

        options.setServerURIs(new String[]{
                "tcp://" + brokerIp + ":" + brokerPort
        });

        options.setAutomaticReconnect(true);
        options.setCleanSession(true);

        factory.setConnectionOptions(options);

        return factory;
    }

    /**
     * MQTT 수신 채널
     */
    @Bean
    public MessageChannel mqttInputChannel() {
        return new DirectChannel();
    }

    @Bean
    public MessageChannel mqttCommandAckInputChannel() {
        return new DirectChannel();
    }

    /**
     * MQTT 발행 채널
     */
    @Bean
    public MessageChannel mqttOutboundChannel() {
        return new DirectChannel();
    }

    /**
     * MQTT Subscriber Adapter
     */
    @Bean
    @ConditionalOnProperty(name = "mqtt.enabled", havingValue = "true", matchIfMissing = true)
    public MessageProducer inbound() {

        String clientId =
                "spring-boot-subscriber-" + System.currentTimeMillis();

        MqttPahoMessageDrivenChannelAdapter adapter =
                new MqttPahoMessageDrivenChannelAdapter(
                         clientId,
                         mqttClientFactory(),
                         RobotMqttTopics.TELEMETRY_FILTER
                 );

        adapter.setCompletionTimeout(5000);
        adapter.setConverter(new DefaultPahoMessageConverter());
        adapter.setQos(1);
        adapter.setOutputChannel(mqttInputChannel());

        return adapter;
    }

    @Bean
    @ConditionalOnProperty(name = "mqtt.enabled", havingValue = "true", matchIfMissing = true)
    public MessageProducer commandAckInbound() {
        MqttPahoMessageDrivenChannelAdapter adapter =
                new MqttPahoMessageDrivenChannelAdapter(
                        "spring-boot-command-ack-subscriber-" + System.currentTimeMillis(),
                        mqttClientFactory(),
                        RobotMqttTopics.COMMAND_ACK_FILTER
                );

        adapter.setCompletionTimeout(5000);
        adapter.setConverter(new DefaultPahoMessageConverter());
        adapter.setQos(1);
        adapter.setOutputChannel(mqttCommandAckInputChannel());
        return adapter;
    }

    /**
     * MQTT Publisher Handler
     */
    @Bean
    @ServiceActivator(inputChannel = "mqttOutboundChannel")
    @ConditionalOnProperty(name = "mqtt.enabled", havingValue = "true", matchIfMissing = true)
    public MessageHandler mqttOutbound() {

        MqttPahoMessageHandler messageHandler =
                new MqttPahoMessageHandler(
                        "spring-boot-publisher-" + System.currentTimeMillis(),
                        mqttClientFactory()
                );

        messageHandler.setAsync(true);
        messageHandler.setDefaultQos(1);
        messageHandler.setDefaultRetained(false);

        return messageHandler;
    }

}
