-- MySQL dump 10.13  Distrib 5.1.73, for redhat-linux-gnu (x86_64)
--
-- Host: localhost    Database: resource_db
-- ------------------------------------------------------
-- Server version	5.1.73

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `build_info`
--

DROP TABLE IF EXISTS `build_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `build_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `build_number` int(11) NOT NULL,
  `git_repo_url` varchar(45) NOT NULL,
  `branch` varchar(45) NOT NULL,
  `commit_id` varchar(45) NOT NULL,
  `hypervisor` varchar(45) NOT NULL,
  `build_date` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `build_number_UNIQUE` (`build_number`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `host`
--

DROP TABLE IF EXISTS `host`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `host` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mac` varchar(45) DEFAULT NULL,
  `ip` varchar(45) DEFAULT NULL,
  `repo_url` varchar(150) DEFAULT NULL,
  `branch` varchar(45) DEFAULT NULL,
  `domain` varchar(45) DEFAULT NULL,
  `hostname` varchar(45) DEFAULT NULL,
  `os` varchar(45) DEFAULT NULL,
  `password` varchar(45) DEFAULT NULL,
  `state` varchar(45) NOT NULL DEFAULT 'free',
  `simulator` varchar(45) NOT NULL DEFAULT 'false',
  `profile` varchar(60) NOT NULL,
  `config_id` int(11) DEFAULT NULL,
  `infra_server` varchar(45) NOT NULL,
  `infra_server_passwd` varchar(45) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mac_UNIQUE` (`mac`),
  UNIQUE KEY `ip_UNIQUE` (`ip`),
  UNIQUE KEY `hostname_UNIQUE` (`hostname`),
  UNIQUE KEY `config_UNIQUE` (`config_id`),
  UNIQUE KEY `config_id_UNIQUE` (`config_id`)
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ip_resource`
--

DROP TABLE IF EXISTS `ip_resource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ip_resource` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ip` varchar(45) DEFAULT NULL,
  `state` varchar(45) NOT NULL DEFAULT 'free',
  `allocated_to_host` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip_UNIQUE` (`ip`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `jobDetails`
--

DROP TABLE IF EXISTS `jobDetails`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `jobDetails` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `job_name` varchar(150) NOT NULL,
  `created` datetime NOT NULL,
  `related_data_path` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `job_name_UNIQUE` (`job_name`)
) ENGINE=MyISAM AUTO_INCREMENT=1720 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mac_resource`
--

DROP TABLE IF EXISTS `mac_resource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mac_resource` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ip` varchar(45) DEFAULT NULL,
  `state` varchar(45) NOT NULL DEFAULT 'free',
  `allocated_to_host` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip_UNIQUE` (`ip`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pull_requests`
--

DROP TABLE IF EXISTS `pull_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pull_requests` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `pr_name` varchar(20) NOT NULL,
  `origin` varchar(64) DEFAULT NULL,
  `tested` varchar(3) NOT NULL,
  `success` varchar(3) DEFAULT NULL,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1496 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `static_config`
--

DROP TABLE IF EXISTS `static_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `static_config` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `configName` varchar(45) NOT NULL,
  `configfile` varchar(150) NOT NULL,
  `state` varchar(45) NOT NULL DEFAULT 'free',
  `simulator` varchar(45) NOT NULL DEFAULT 'false',
  `profile` varchar(60) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`),
  UNIQUE KEY `configName_UNIQUE` (`configName`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `static_host_info`
--

DROP TABLE IF EXISTS `static_host_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `static_host_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hostname` varchar(150) NOT NULL,
  `ip` varchar(45) NOT NULL,
  `netmask` varchar(45) NOT NULL,
  `gateway` varchar(45) NOT NULL,
  `mac` varchar(45) NOT NULL,
  `ipmi_hostname` varchar(45) NOT NULL,
  `ipmi_password` varchar(45) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `hostname_UNIQUE` (`hostname`),
  UNIQUE KEY `ip_UNIQUE` (`ip`),
  UNIQUE KEY `mac_UNIQUE` (`mac`),
  UNIQUE KEY `ipmi_hostname_UNIQUE` (`ipmi_hostname`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `systemvm_template`
--

DROP TABLE IF EXISTS `systemvm_template`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `systemvm_template` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `branch` varchar(45) NOT NULL,
  `download_url` varchar(200) NOT NULL,
  `hypervisor_type` varchar(45) NOT NULL,
  `bits` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2016-01-31 21:28:24
